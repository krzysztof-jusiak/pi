from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from time import sleep
from subprocess import call
import SocketServer
import RPi.GPIO as GPIO
import sys, os, time, cv2, threading
from pybrain.datasets import SupervisedDataSet
from pybrain.datasets import UnsupervisedDataSet
from pybrain.tools.shortcuts import buildNetwork
from pybrain.supervised import BackpropTrainer
from random import shuffle
import numpy as np
import pickle
import math

GPIO.setwarnings(False)

GPIO.setmode(GPIO.BOARD)

Motor1A = 35 #GP19
Motor1B = 37 #GP26
Motor1E = 33 #GP13

#engine left
GPIO.setup(Motor1A, GPIO.OUT)
GPIO.setup(Motor1B, GPIO.OUT)
GPIO.setup(Motor1E, GPIO.OUT)
e1 = GPIO.PWM(Motor1E, 100) # freq, in hertz
e1.start(0)

Motor2A = 16 #GP24
Motor2B = 12 #GP18
Motor2E = 18 #GP23

#engine right
GPIO.setup(Motor1A, GPIO.OUT)
GPIO.setup(Motor2A, GPIO.OUT)
GPIO.setup(Motor2B, GPIO.OUT)
GPIO.setup(Motor2E, GPIO.OUT)
e2 = GPIO.PWM(Motor2E, 100) # freq, in hertz
e2.start(0)

LED = 36 #GP16
GPIO.setup(LED, GPIO.OUT)

SONAR_TRIGGER = 31 #GB6
SONAR_ECHO = 29 #GB5

SIZE=80*50
OUTPUT=2

def sonar_distance(trig_pin = SONAR_TRIGGER, echo_pin = SONAR_ECHO, sample_size = 7, sample_wait = 0.1, temperature = 20):
  speed_of_sound = 331.3 * math.sqrt(1+(temperature / 273.15))
  sample = []
  GPIO.setmode(GPIO.BOARD)
  GPIO.setup(trig_pin, GPIO.OUT)
  GPIO.setup(echo_pin, GPIO.IN)
  for distance_reading in range(sample_size):
      GPIO.output(trig_pin, GPIO.LOW)
      time.sleep(sample_wait)
      GPIO.output(trig_pin, True)
      time.sleep(0.00001)
      GPIO.output(trig_pin, False)
      while GPIO.input(echo_pin) == 0:
          sonar_signal_off = time.time()
      while GPIO.input(echo_pin) == 1:
          sonar_signal_on = time.time()
      time_passed = sonar_signal_on - sonar_signal_off
      distance_cm = time_passed * ((speed_of_sound * 100) / 2)
      sample.append(distance_cm)
  sorted_sample = sorted(sample)
  GPIO.cleanup((trig_pin, echo_pin))
  return sorted_sample[sample_size // 2]

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
  pass

class HTTPHandler(BaseHTTPRequestHandler):
    frames = 30
    led = False
    train = False
    auto = False
    debug = False
    debug_step = False
    left = 0
    right = 0
    can_measure = True
    distance = 0

    def do_GET(self):
        print self.path
        if self.path == "/":
          self.send_response(200)
          self.send_header('Content-type', 'text/html')
          self.send_header("Access-Control-Allow-Origin", "*")
          self.end_headers()
          with open(os.getcwd() + '/index.html') as f: self.wfile.write(f.read())

        elif self.path.endswith(".png"):
          self.send_response(200)
          self.send_header('Content-type', 'image/png')
          self.send_header("Access-Control-Allow-Origin", "*")
          self.end_headers()
          with open(os.getcwd() + self.path) as f: self.wfile.write(f.read())

        elif self.path.startswith("/train:on"):
          print "training..."
          cap = cv2.VideoCapture(0)
          count = 0
          cap.set(3, 80)
          cap.set(4, 50)
          HTTPHandler.train = True
          while cap.isOpened() and HTTPHandler.train:
            time.sleep(0.2)
            if HTTPHandler.left > 40 and HTTPHandler.right > 40:
              ret, frame = cap.read()
              gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
              print "frame: ", count, HTTPHandler.left, HTTPHandler.right
              cv2.imwrite("frame_{count:04d}_{left:03d}_{right:03d}.png".format(count=count, left=HTTPHandler.left, right=HTTPHandler.right), gray)
              count = count + 1
          cap.release()

        elif self.path.startswith("/train:off"):
          HTTPHandler.train = False

        elif self.path.startswith("/debug:on"):
          HTTPHandler.debug = True
          
        elif self.path.startswith("/debug:off"):
          HTTPHandler.debug = False

        elif self.path.startswith("/debug:step"):
          HTTPHandler.debug_step = True

        elif self.path.startswith("/auto:on"):
          self.send_response(200)
          self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
          self.end_headers()
          print "run"
          file = "net.obj"
          fileObject = open(file, 'r')
          network = pickle.load(fileObject)
          error = 0.02;
          fileObject.close()
          print "..."
          cap = cv2.VideoCapture(0)
          cap.set(3, 80)
          cap.set(4, 50)
          HTTPHandler.auto = True
          while cap.isOpened() and HTTPHandler.auto:
            while HTTPHandler.debug and not HTTPHandler.debug_step:
              time.sleep(0.1)
            HTTPHandler.debug_step = False
        
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            crop = gray[25:,]
            inverted = (255 - crop)
            bw = cv2.threshold(inverted, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            array = bw.reshape(1, SIZE/2).astype(np.float32)
            dataset = UnsupervisedDataSet(SIZE/2)
            dataset.addSample(array)
            active = network.activateOnDataset(dataset)[0]

            if HTTPHandler.distance >= 10: #cm
              HTTPHandler.left = 85 if active[1] > 0.9 else 0
              HTTPHandler.right = 85 if active[0] > 0.9 else 0
            else:
              HTTPHandler.left = 0
              HTTPHandler.right = 0

            print "auto: " + str(HTTPHandler.left) + ":" + str(HTTPHandler.right)

            #engine left
            GPIO.output(Motor1A, GPIO.LOW)
            GPIO.output(Motor1B, GPIO.HIGH)
            e1.ChangeDutyCycle(HTTPHandler.left)

            #engine right
            GPIO.output(Motor2A, GPIO.LOW)
            GPIO.output(Motor2B, GPIO.HIGH)
            e2.ChangeDutyCycle(HTTPHandler.right)

            steps_image = np.zeros((360, 640), np.uint8)
            steps_image.fill(255)
            steps_image[50+50:50+50+50,       50+25+25:80+25+25+50] = gray
            steps_image[50+50+25:50+25+50+25, 50+25+85+25:25+80+80+5+25+50] = crop
            steps_image[50+50+25:50+25+50+25, 50+25+25+160+5+5:80+80+80+5+5+25+25+50] = inverted
            steps_image[50+50+25:50+25+50+25, 50+25+25+240+5+5+5:80+80+80+80+5+5+5+25+25+50] = bw
            cv2.putText(steps_image, "net: '" + file + "', error: " + str(error), (100, 75), cv2.FONT_HERSHEY_PLAIN, 1.0, 0, 1)
            cv2.putText(steps_image, "activate: " + str(active), (100, 200), cv2.FONT_HERSHEY_PLAIN, 1.0, 0, 1)
            cv2.putText(steps_image, "obstacle: " + str(HTTPHandler.distance) + " cm", (100, 225), cv2.FONT_HERSHEY_PLAIN, 1.0, 0, 1)
            cv2.putText(steps_image, "auto: " + str(HTTPHandler.left) + ", " + str(HTTPHandler.right), (100, 250), cv2.FONT_HERSHEY_PLAIN, 1.0, 0, 1)
            result, buf = cv2.imencode('.jpg', steps_image, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            assert result

            self.wfile.write("--jpgboundary")
            self.send_header('Content-type','image/jpeg')
            self.send_header('Content-length', str(len(buf)))
            self.end_headers()
            self.wfile.write(bytearray(buf))
            self.wfile.write('\r\n')
          cap.release()

        elif self.path.startswith("/auto:off"):
          HTTPHandler.auto = False

        elif self.path.startswith("/ping"):
          if HTTPHandler.can_measure:
            HTTPHandler.can_measure = False
            HTTPHandler.distance = sonar_distance()

            GPIO.output(LED, GPIO.HIGH if HTTPHandler.led else GPIO.LOW)
            HTTPHandler.led ^= True

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(str(HTTPHandler.distance))
            self.wfile.close()
            HTTPHandler.measure = True

        elif self.path.startswith("/forward"):
          HTTPHandler.left = max(0, int(self.path.split(':')[1]))
          HTTPHandler.right = max(0, int(self.path.split(':')[2]))
          print "forward: " + str(HTTPHandler.left) + ":" + str(HTTPHandler.right)

          #engine left
          GPIO.output(Motor1A, GPIO.LOW)
          GPIO.output(Motor1B, GPIO.HIGH)
          e1.ChangeDutyCycle(HTTPHandler.left)

          #engine right
          GPIO.output(Motor2A, GPIO.LOW)
          GPIO.output(Motor2B, GPIO.HIGH)
          e2.ChangeDutyCycle(HTTPHandler.right)

        elif self.path.startswith("/reverse"):
          HTTPHandler.left = max(0, int(self.path.split(':')[1]))
          HTTPHandler.right = max(0, int(self.path.split(':')[2]))
          print "reverse: " + str(HTTPHandler.left) + ":" + str(HTTPHandler.right)

          #engine left
          GPIO.output(Motor1A, GPIO.HIGH)
          GPIO.output(Motor1B, GPIO.LOW)
          e1.ChangeDutyCycle(HTTPHandler.left)

          #engine right
          GPIO.output(Motor2A, GPIO.HIGH)
          GPIO.output(Motor2B, GPIO.LOW)
          e2.ChangeDutyCycle(HTTPHandler.right)

        elif self.path.startswith("/camera"):
          status = self.path.split(':')[1]
          print "camera: " + status

          if status == "on":
            call("mjpg_streamer -i 'input_uvc.so -n -f " + str(HTTPHandler.frames) + " -r 640x360' -o 'output_http.so -p 10088 -w /usr/local/www' &", shell=True)
          else:
            call("pkill -9 mjpg_streamer", shell=True)

        elif self.path.startswith("/off"):
          call("halt", shell=True)

server_address = ('', 80)
httpd = ThreadedHTTPServer(server_address, HTTPHandler)

try:
    GPIO.output(LED, GPIO.HIGH)
    httpd.serve_forever()
except:
    httpd.server_close()
    e1.stop()
    e2.stop()
    GPIO.output(Motor1E, GPIO.LOW)
    GPIO.output(Motor2E, GPIO.LOW)
    GPIO.cleanup()
    call("pkill -9 mjpg_streamer", shell=True)

