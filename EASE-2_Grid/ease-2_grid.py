import numpy as np

lats = np.fromfile('EASE2_M36km.lats.964x406x1.double', dtype=np.float64).reshape((406, 964))
lons = np.fromfile('EASE2_M36km.lons.964x406x1.double', dtype=np.float64).reshape((406, 964))

grid_row = 46
grid_column = 470

lat_val = lats[grid_row, grid_column]
lon_val = lons[grid_row, grid_column]