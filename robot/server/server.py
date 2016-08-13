from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from time import sleep
from subprocess import call
import SocketServer
import RPi.GPIO as GPIO
import sys

Motor1A = 35 #GP19
Motor1B = 37 #GP26
Motor1E = 33 #GP13

Motor2A = 16 #GP24
Motor2B = 12 #GP18
Motor2E = 18 #GP23

GPIO.setmode(GPIO.BOARD)

#engine left
GPIO.setup(Motor1A, GPIO.OUT)
GPIO.setup(Motor1B, GPIO.OUT)
GPIO.setup(Motor1E, GPIO.OUT)
e1 = GPIO.PWM(Motor1E, 100) # freq, in hertz
e1.start(0)

#engine right
GPIO.setup(Motor1A, GPIO.OUT)
GPIO.setup(Motor2A, GPIO.OUT)
GPIO.setup(Motor2B, GPIO.OUT)
GPIO.setup(Motor2E, GPIO.OUT)
e2 = GPIO.PWM(Motor2E, 100) # freq, in hertz
e2.start(0)

class HTTPHandler(BaseHTTPRequestHandler):
    frames = 30
    def do_GET(self):
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
          e1.ChangeDutyCycle(left)

          #engine right
          GPIO.output(Motor2A, GPIO.LOW)
          GPIO.output(Motor2B, GPIO.HIGH)
          e2.ChangeDutyCycle(right)

        elif self.path.startswith("/reverse"):
          left = self.path.split(':')[1]
          right = self.path.split(':')[2]
          print "reverse: " + left + ":" + right

          #engine left
          GPIO.output(Motor1A, GPIO.HIGH)
          GPIO.output(Motor1B, GPIO.LOW)
          e1.ChangeDutyCycle(left)

          #engine right
          GPIO.output(Motor2A, GPIO.HIGH)
          GPIO.output(Motor2B, GPIO.LOW)
          e2.ChangeDutyCycle(right)

        elif self.path.startswith("/camera"):
          status = self.path.split(':')[1]
          print "camera: " + status

          if status == "on":
            call("mjpg_streamer -i 'input_uvc.so -n -f " + str(HTTPHandler.frames) + " -r 640x360' -o 'output_http.so -p 10088 -w /usr/local/www' &", shell=True)
          else:
            call("pkill -9 mjpg_streamer", shell=True)

        elif self.path.startswith("/off"):
          call("halt", shell=True)

def run(server_class=HTTPServer, handler_class=HTTPHandler, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

try:
    run()
except:
    e1.stop()
    e2.stop()
    GPIO.output(Motor1E, GPIO.LOW)
    GPIO.output(Motor2E, GPIO.LOW)
    GPIO.cleanup()
    call("pkill -9 mjpg_streamer", shell=True)
