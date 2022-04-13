# Tyler Singleton
# Final Project for GPGN470

# Necessary Libraries
import numpy as np

# Data File Extraction
import netCDF4 as nc

# Image Manipulation
import matplotlib.pyplot as plt
import pyqtgraph as pg

filename = r"Land_Cover\Global_300m.nc"
dataset = nc.Dataset(filename)

#print(dataset)
for i in dataset.__dict__:
    print(i)

print("------------")

for i in dataset.dimensions.values():
    print(i)

# print("------------")
# for i in dataset.variables.values():
#     print(i)

print("------------")
print(dataset['lccs_class'].shape)

# plt.figure()
# plt.imshow(dataset['lccs_class'][0])
# plt.show()

import time

# pyqtgraph time test
start_time = time.time()
pg.image(dataset['lccs_class'][0].T)

print("%s" %(time.time() - start_time))

# matplotlib time test
start_time = time.time()
plt.figure()
plt.imshow(dataset['lccs_class'][0])
plt.show()

print("%s" %(time.time() - start_time))