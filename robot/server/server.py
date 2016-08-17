from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from time import sleep
from subprocess import call
import SocketServer
import RPi.GPIO as GPIO
import sys
import os

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

class HTTPHandler(BaseHTTPRequestHandler):
    frames = 30
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
        if self.path.startswith("/frames"):
          HTTPHandler.frames = int(self.path.split(':')[1])
          print "frames: " + str(HTTPHandler.frames)
        elif self.path.startswith("/ping"):
          self.send_response(200)
          self.send_header('Content-type', 'text/html')
          self.send_header("Access-Control-Allow-Origin", "*")
          self.end_headers()
        elif self.path.startswith("/forward"):
          left = self.path.split(':')[1]
          right = self.path.split(':')[2]
          print "forward: " + left + ":" + right

          #engine left
          GPIO.output(Motor1A, GPIO.LOW)
          GPIO.output(Motor1B, GPIO.HIGH)
          e1.ChangeDutyCycle(int(left))

          #engine right
          GPIO.output(Motor2A, GPIO.LOW)
          GPIO.output(Motor2B, GPIO.HIGH)
          e2.ChangeDutyCycle(int(right))

        elif self.path.startswith("/reverse"):
          left = self.path.split(':')[1]
          right = self.path.split(':')[2]
          print "reverse: " + left + ":" + right

          #engine left
          GPIO.output(Motor1A, GPIO.HIGH)
          GPIO.output(Motor1B, GPIO.LOW)
          e1.ChangeDutyCycle(int(left))

          #engine right
          GPIO.output(Motor2A, GPIO.HIGH)
          GPIO.output(Motor2B, GPIO.LOW)
          e2.ChangeDutyCycle(int(right))

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
