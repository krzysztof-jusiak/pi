import tensorflow as tf
import scipy.misc
import model
import cv2
import os
import time
from subprocess import call

sess = tf.InteractiveSession()
saver = tf.train.Saver()
saver.restore(sess, "net/model.ckpt")

img = cv2.imread('www/img/sw.png',0)
rows,cols = img.shape

smoothed_angle = 0

list = []
for file in sorted(os.listdir("data")):
  if file.endswith(".jpg"):
    list.append(file)

i = 0
while(cv2.waitKey(10) != ord('q')):
  cv2.imshow("steering wheel", img)
  file = list[i]
  frame = int(file.split('_')[1])
  left = int(file.split('_')[2])
  right = int(file.split('_')[3].split('.')[0])
  image = scipy.misc.imresize(scipy.misc.imread("data/" + file)[-150:], [66, 200]) / 255.0
  original = float((left) - (right)) * 4.0 
  degrees = 4.0 * (model.y.eval(feed_dict={model.x: [image], model.keep_prob: 1.0})[0][0] * 180.0 / scipy.pi + 15.0)
  print("Predicted steering angle: " + str(degrees) + ", " + str(original))
  cv2.imshow("frame", image)
  #make smooth angle transitions by turning the steering wheel based on the difference of the current angle
  #and the predicted angle
  smoothed_angle += 0.2 * pow(abs((degrees - smoothed_angle)), 2.0 / 3.0) * (degrees - smoothed_angle) / abs(degrees - smoothed_angle)
  M = cv2.getRotationMatrix2D((cols/2,rows/2),-smoothed_angle,1)
  dst = cv2.warpAffine(img,M,(cols,rows))
  cv2.imshow("steering wheel", dst)
  i += 1
  time.sleep(0.1)

cv2.destroyAllWindows()
