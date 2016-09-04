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
    data = []
    for file in sorted(os.listdir("data")):
        if file.endswith(".png"):
            frame = int(file.split('_')[1])
            left = int(file.split('_')[2])
            right = int(file.split('_')[3].split('.')[0])
            image = cv2.imread("data/" + file, cv2.IMREAD_GRAYSCALE)
            array = image.reshape(1, SIZE).astype(np.float32)
            if frame <= 630:
              left = 1
              right = 0
            elif frame > 630 and frame <= 1671:
              left = 0
              right = 1
            else:
              left = 1
              right = 1
            data.append([array, left, right])
    shuffle(data)
    data_set = SupervisedDataSet(SIZE, OUTPUT)
    for d in data:
      data_set.addSample(d[0][0], [d[1], d[2]])

    return data_set

def training(d):
    print "train..."
    n = buildNetwork(d.indim, 64, d.outdim, recurrent=True, bias=True)
    t = BackpropTrainer(n, d, learningrate = 0.001, momentum = 0.0)
    try:
      for epoch in range(0, 1000):
        print t.train()
    except:
        return n
    return n

def test(network):
    c = 0
    ok = 0
    for file in sorted(os.listdir("data")):
        if file.endswith(".png"):
          image = cv2.imread("data/" + file, cv2.IMREAD_GRAYSCALE)
          array = image.reshape(1, SIZE).astype(np.float32)
          dataset = UnsupervisedDataSet(SIZE)
          dataset.addSample(array)
          frame = int(file.split('_')[1])
          left = int(file.split('_')[2])
          right = int(file.split('_')[3].split('.')[0])
          active = network.activateOnDataset(dataset)[0]
#          active_left = 1 if active[0] > 0.9 else 0
#          active_right = 1 if active[1] > 0.9 else 0
          print frame, left, right, active
#          print file, [lef, active_left, active[0]], [right_value, active_right, active[1]], (left_value == active_left and right_value == active_right)
#          ok += (left_value == active_left and right_value == active_right)
#          c = c + 1
#    print c, ok, (ok*1.0/c) * 100.0

trainingdata = make_dataset()
network = training(trainingdata)
NetworkWriter.writeToFile(network, 'net.xml')
network = NetworkReader.readFrom('net.xml')
test(network)
