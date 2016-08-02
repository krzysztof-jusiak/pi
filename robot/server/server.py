from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from time import sleep
from subprocess import call
import SocketServer
import RPi.GPIO as GPIO
import sys

GPIO.setmode(GPIO.BOARD)

Motor1A = 18 #GP23
Motor1B = 16 #GP24
Motor1E = 12 #GP18
Motor2A = 35 #GP19
Motor2B = 37 #GP26
Motor2E = 33 #GP13

GPIO.setup(Motor1A, GPIO.OUT)
GPIO.setup(Motor1B, GPIO.OUT)
GPIO.setup(Motor1E, GPIO.OUT)
e1 = GPIO.PWM(Motor1E, 100) # freq, in hertz
e1.start(0)

GPIO.setup(Motor2A, GPIO.OUT)
GPIO.setup(Motor2B, GPIO.OUT)
GPIO.setup(Motor2E, GPIO.OUT)
e2 = GPIO.PWM(Motor2E, 100) # freq, in hertz
e2.start(0)

class S(BaseHTTPRequestHandler)
    def do_GET(self):
        self.send_response(200)

        if self.path.startswith("/forward"):
          left = self.path.split(':')[1]
          right = self.path.split(':')[2]
          print "forward: " + left + ":" + right

          #engine left
          GPIO.output(Motor1A,GPIO.LOW)
          GPIO.output(Motor1B,GPIO.HIGH)
          e2.ChangeDutyCycle(int(left))

          #engine right
          GPIO.output(Motor2A,GPIO.LOW)
          GPIO.output(Motor2B,GPIO.HIGH)
          e1.ChangeDutyCycle(int(right))

        elif self.path.startswith("/reverse"):
          left = self.path.split(':')[1]
          right = self.path.split(':')[2]
          print "reverse: " + left + ":" + right

          #engine left
          GPIO.output(Motor1A,GPIO.HIGH)
          GPIO.output(Motor1B,GPIO.LOW)
          e2.ChangeDutyCycle(int(left))

          #engine right
          GPIO.output(Motor2A,GPIO.HIGH)
          GPIO.output(Motor2B,GPIO.LOW)
          e1.ChangeDutyCycle(int(right))

        elif self.path.startswith("/camera"):
          status = self.path.split(':')[1]
          if status == "on":
            call("sudo modprobe bcm2835-v4l2", shell=True)
            call("mjpg_streamer -i 'input_uvc.so -n -f 5 -r 640x360' -o 'output_http.so -p 10088 -w /usr/local/www'", shell=True)
          else:
            call("sudo pkill -9 mjpg_streamer", shell=True)
            call("sudo rmmod bcm2835-v4l2", shell=True)

        elif self.path.startswith("/off"):
          call("sudo halt", shell=True)

def run(server_class=HTTPServer, handler_class=S, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

try:
    run()
except KeyboardInterrupt:
    GPIO.output(Motor1E,GPIO.LOW)
    GPIO.output(Motor2E,GPIO.LOW)
    GPIO.cleanup()
