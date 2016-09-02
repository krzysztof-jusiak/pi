import sys
sys.path.append('/usr/local/lib/python2.7/site-packages')
from pybrain.datasets import SupervisedDataSet
from pybrain.datasets import UnsupervisedDataSet
from pybrain.tools.shortcuts import buildNetwork
from pybrain.tools.xml.networkwriter import NetworkWriter
from pybrain.tools.xml.networkreader import NetworkReader
from pybrain.supervised import BackpropTrainer
from random import shuffle
import numpy as np
import cv2
import os

SIZE=80*50
OUTPUT=2

def make_dataset():
    print "prepare data..."
    data = SupervisedDataSet(SIZE, OUTPUT)
    for file in os.listdir("data"):
        if file.endswith(".png"):
            left = int(file.split('_')[2])
            right = int(file.split('_')[3].split('.')[0])
            image = cv2.imread("data/" + file, cv2.IMREAD_GRAYSCALE)
            array = image.reshape(1, SIZE).astype(np.float32)
#            left_value = 2 if left >= 60 else 1 if left >= 40 and left < 60 else 0
#            right_value = 2 if right >= 60 else 1 if right >= 40 and right < 60 else 0
            if abs(left -right) > 15:
              left_value = 1 if left > right else 0
              right_value = 1 if right > left else 0
            else:
              left_value = 1
              right_value = 1

            data.addSample(array, [left_value, right_value])
#            print file, abs(left - right), left_value, right_value
    return data


def training(d):
    print "train..."
    n = buildNetwork(d.indim, 16, d.outdim, recurrent=True, bias=True)
    t = BackpropTrainer(n, d, learningrate = 0.01, momentum = 0, verbose = True)
    for epoch in range(0, 100):
      if t.train() < 0.01:
        pass
    return n

def test(network):
    c = 0
    ok = 0
    for file in os.listdir("data"):
        if file.endswith(".png"):
          image = cv2.imread("data/" + file, cv2.IMREAD_GRAYSCALE)
          array = image.reshape(1, SIZE).astype(np.float32)
          dataset = UnsupervisedDataSet(SIZE)
          dataset.addSample(array)  
          left = int(file.split('_')[2])
          right = int(file.split('_')[3].split('.')[0])
          active = network.activateOnDataset(dataset)[0]
          if abs(left -right) > 15:
            left_value = 1 if left > right else 0
            right_value = 1 if right > left else 0
          else:
            left_value = 1
            right_value = 1

          active_left = 1 if active[0] > 0.7 else 0
          active_right = 1 if active[1] > 0.7 else 0
          print file, [left_value, active_left, active[0]], [right_value, active_right, active[1]], (left_value == active_left and right_value == active_right)
          ok += (left_value == active_left and right_value == active_right)
          c = c + 1
    print c, ok, (ok*1.0/c) * 100.0

trainingdata = make_dataset()
network = training(trainingdata)
NetworkWriter.writeToFile(network, 'net.xml')
network = NetworkReader.readFrom('net.xml')
test(network)
