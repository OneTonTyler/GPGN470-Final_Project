# Data File Extraction
from shapely.geometry import Point

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas
import xarray as xr

# File IO
import glob

# Extract all files
cygnss_dataset = [xr.open_dataset(dataset) for dataset in glob.glob('Global/*.nc')]

# Combine cygnss datasets into a single pandas dataframe
df = [pd.DataFrame({'SNR': dataset['ddm_snr'].values.ravel(),
                    'Latitude': dataset['sp_lat'].values.ravel(),
                    'Longitude': dataset['sp_lon'].values.ravel() - 180}) for dataset in cygnss_dataset]
df = pd.concat(df, ignore_index=True)

# Set lon and lat at point coordinates
df['Coordinates'] = list(zip(df.Longitude, df.Latitude))
df['Coordinates'] = df['Coordinates'].apply(Point)

# Convert pandas dataframe object into a geopandas dataframe object
gdf = geopandas.GeoDataFrame(df, geometry='Coordinates')
gdf = gdf.set_crs('epsg:4326')

# Cip geodataframe with respect to shapefile
mask = geopandas.read_file(r'C:\Users\Projects\Desktop\GPGN 470\Final_Project\Shape_Files\Mexico\Mexico.shp')
gdf_clipped = geopandas.clip(gdf, mask)

# Plot the geodataframe
gdf_clipped.plot('SNR', cmap='viridis', markersize=0.1)
plt.show()
