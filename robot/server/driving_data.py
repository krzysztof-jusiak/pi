import scipy.misc
import random
import os

xs = []
ys = []

#points to the end of the last batch
batch_pointer = 0

for file in sorted(os.listdir("data")):
  if file.endswith(".jpg"):
    left = int(file.split('_')[2])
    right = int(file.split('_')[3].split('.')[0])
    xs.append("data/" + file)
    ys.append(float(left - right) * scipy.pi / 180)

#get number of images
num_images = len(xs)

#shuffle list of images
c = list(zip(xs, ys))
random.shuffle(c)
xs, ys = zip(*c)

def LoadBatch(batch_size):
    global batch_pointer
    x_out = []
    y_out = []
    for i in range(0, batch_size):
        x_out.append(scipy.misc.imresize(scipy.misc.imread(xs[(batch_pointer + i) % num_images])[-150:], [66, 200]) / 255.0)
        y_out.append([ys[(batch_pointer + i) % num_images]])
    batch_pointer += batch_size
    return x_out, y_out
