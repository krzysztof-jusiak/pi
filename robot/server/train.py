import sys
sys.path.append('/usr/local/lib/python2.7/site-packages')
from pybrain.datasets import SupervisedDataSet
from pybrain.datasets import UnsupervisedDataSet
from pybrain.tools.shortcuts import buildNetwork
from pybrain.tools.xml.networkwriter import NetworkWriter
from pybrain.tools.xml.networkreader import NetworkReader
from pybrain.supervised import BackpropTrainer
import numpy as np
import cv2
import os

SIZE=80*50
#IMREAD_GRAYSCALE

def make_dataset():
    print "prepare data..."
    data = SupervisedDataSet(SIZE, 2)
    for file in os.listdir("frames"):
        if file.endswith(".png"):
            left = int(file.split('_')[2])
            right = int(file.split('_')[3].split('.')[0])
            image = cv2.imread("frames/" + file, cv2.IMREAD_GRAYSCALE)
            array = image.reshape(1, SIZE).astype(np.float32)
            left_value = right_value = 1
            if abs(left - right) > 20:
                left_value = 1 if left > right else 0
                right_value = 1 if right > left else 0
            data.addSample(array, [left_value, right_value])
    return data


def training(d):
    print "train..."
    n = buildNetwork(d.indim, 32, d.outdim, recurrent=True)
    t = BackpropTrainer(n, d, learningrate = 0.001, momentum = 0, verbose = True)
    for epoch in range(0, 300):
        t.train()
    return n

def test(network):
    image = cv2.imread("frames/frame_0205_059_032.jpg.png", cv2.IMREAD_GRAYSCALE)
    array = image.reshape(1, SIZE).astype(np.float32)
    dataset = UnsupervisedDataSet(SIZE)
    dataset.addSample(array)  
    print network.activateOnDataset(dataset)[0]

trainingdata = make_dataset()
network = training(trainingdata)
NetworkWriter.writeToFile(network, 'net.xml')
network = NetworkReader.readFrom('net.xml')
#test(network)
