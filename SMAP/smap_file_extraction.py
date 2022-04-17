# Data File Extraction
import json

from shapely.geometry import mapping, Point
from rioxarray.merge import merge_datasets

import numpy as np
import h5py
import pandas as pd
import xarray as xr
import rioxarray as rxr
import geopandas
import matplotlib.pyplot as plt

# File IO
import glob

# Extract hdf5 files
smap_dataset = [h5py.File(dataset) for dataset in glob.glob('Global/*.h5')]

# Convert into pandas dataframe object
df = [pd.DataFrame({
    'Soil_Moisture': dataset['Soil_Moisture_Retrieval_Data_AM']['soil_moisture'][:].ravel(),
    'Latitude': dataset['Soil_Moisture_Retrieval_Data_AM']['latitude'][:].ravel(),
    'Longitude': dataset['Soil_Moisture_Retrieval_Data_AM']['longitude'][:].ravel()
}) for dataset in smap_dataset]
df = pd.concat(df, ignore_index=True)

# Set lon and lat at point coordinates
df['Coordinates'] = list(zip(df.Longitude, df.Latitude))
df['Coordinates'] = df['Coordinates'].apply(Point)

# Convert pandas dataframe object into a geopandas dataframe object
gdf = geopandas.GeoDataFrame(df.query('Soil_Moisture >= 0'), geometry='Coordinates')
gdf = gdf.set_crs('epsg:4326')
gdf.drop_duplicates(subset='Coordinates', inplace=True)

# Cip geodataframe with respect to shapefile
mask = geopandas.read_file(r'C:\Users\Projects\Desktop\GPGN 470\Final_Project\Shape_Files\Mexico\Mexico.shp')
gdf_clipped = geopandas.clip(gdf, mask)
gdf_clipped.reset_index(drop=True, inplace=True)

# Plot the geodataframe
gdf_clipped.plot('Soil_Moisture', cmap='viridis', markersize=0.1)
plt.show()
