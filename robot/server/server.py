from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
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

class HTTPHandler(BaseHTTPRequestHandler):
    frames = 30
    led = False
    train = False
    train_thread = None
    left = 0
    right = 0
    distance = -1

    def train(self):
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

        elif self.path.startswith("/train"):
          print "training..."
          HTTPHandler.train_thread = threading.Thread(target=self.train)
          HTTPHandler.train_thread.start()

        elif self.path.startswith("/stop"):
          HTTPHandler.train = False
          HTTPHandler.train_thread.join()

        elif self.path.startswith("/auto:on"):
          self.send_response(200)
          self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
          self.end_headers()
          print "run"
          fileObject = open('net.obj','r')
          network = pickle.load(fileObject)
          fileObject.close()
          print "..."
          cap = cv2.VideoCapture(0)
          cap.set(3, 80)
          cap.set(4, 50)
          while cap.isOpened():
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            array = gray.reshape(1, SIZE).astype(np.float32)
            dataset = UnsupervisedDataSet(SIZE)
            dataset.addSample(array)
            active = network.activateOnDataset(dataset)[0]
            HTTPHandler.left = 85 if active[1] > 0.7 else 50
            HTTPHandler.right = 85 if active[0] > 0.7 else 50
#            HTTPHandler.left = min(100, max(0, int(active[0])))
#            HTTPHandler.right = min(100, max(0, int(active[1])))

            print "auto: " + str(HTTPHandler.left) + ":" + str(HTTPHandler.right)

            #engine left
            GPIO.output(Motor1A, GPIO.LOW)
            GPIO.output(Motor1B, GPIO.HIGH)
            e1.ChangeDutyCycle(HTTPHandler.left)

            #engine right
            GPIO.output(Motor2A, GPIO.LOW)
            GPIO.output(Motor2B, GPIO.HIGH)
            e2.ChangeDutyCycle(HTTPHandler.right)

            self.wfile.write("--jpgboundary")
            self.send_header('Content-type','image/jpeg')
            self.send_header('Content-length',len(gray))
            self.end_headers()
            self.wfile.write(gray)

        elif self.path.startswith("/ping"):
          if HTTPHandler.distance == -1:
            HTTPHandler.distance = 0
            GPIO.output(SONAR_TRIGGER, GPIO.HIGH)
            time.sleep(0.00001)
            GPIO.output(SONAR_TRIGGER, GPIO.LOW)

            GPIO.wait_for_edge(SONAR_ECHO, GPIO_RISING, timeout=500)
            pulse_start = time.time()
            GPIO.wait_for_edge(SONAR_ECHO, GPIO.FALLING, timeout=500)
            pulse_end = time.time()

            pulse_duration = pulse_end - pulse_start
            HTTPHandler.distance = pulse_duration * 17150
            HTTPHandler.distance = round(distance, 2)

            if HTTPHandler.distance < 2 or HTTPHandler.distance > 400:
              HTTPHandler.distance = 0

            GPIO.output(SONAR_TRIGGER, GPIO.LOW)
            GPIO.output(LED, GPIO.HIGH if HTTPHandler.led else GPIO.LOW)
            HTTPHandler.led^=True

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(str(HTTPHandler.distance))
            self.wfile.close()
            HTTPHandler.distance = -1

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
httpd = HTTPServer(server_address, HTTPHandler)

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

