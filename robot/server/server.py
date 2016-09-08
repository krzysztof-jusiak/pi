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
GPIO.setup(SONAR_TRIGGER, GPIO.OUT)
GPIO.setup(SONAR_ECHO, GPIO.IN)

SIZE=80*50
OUTPUT=2

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
    measure = -1
    distance = 0

    def do_GET(self):
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

            if HTTPHandler.distance >= 20: #cm
              HTTPHandler.left = 85 if active[1] > 0.9 else 50
              HTTPHandler.right = 85 if active[0] > 0.9 else 50
#            HTTPHandler.left = min(100, max(0, int(active[0])))
#            HTTPHandler.right = min(100, max(0, int(active[1])))
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
            cv2.putText(steps_image, "net: '" + file + "', error: " + str(errror), (100, 75), cv2.FONT_HERSHEY_PLAIN, 1.0, 0, 1)
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
          if HTTPHandler.measure == -1:
            HTTPHandler.measure = 0
            GPIO.output(SONAR_TRIGGER, GPIO.HIGH)
            time.sleep(0.00001)
            GPIO.output(SONAR_TRIGGER, GPIO.LOW)

            GPIO.wait_for_edge(SONAR_ECHO, GPIO.RISING, timeout=500)
            pulse_start = time.time()
            GPIO.wait_for_edge(SONAR_ECHO, GPIO.FALLING, timeout=500)
            pulse_end = time.time()

            pulse_duration = pulse_end - pulse_start
            HTTPHandler.measure = pulse_duration * 17150
            HTTPHandler.measure = round(HTTPHandler.measure, 2)

            if HTTPHandler.measure < 2 or HTTPHandler.measure > 400:
              HTTPHandler.measure = 0

            HTTPHandler.distance = HTTPHandler.measure

            GPIO.output(SONAR_TRIGGER, GPIO.LOW)
            GPIO.output(LED, GPIO.HIGH if HTTPHandler.led else GPIO.LOW)
            HTTPHandler.led ^= True

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(str(HTTPHandler.measure))
            self.wfile.close()
            HTTPHandler.measure = -1

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
    GPIO.output(SONAR_TRIGGER, GPIO.LOW)
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

