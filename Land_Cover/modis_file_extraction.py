# Necessary imports
import matplotlib.pyplot as plt

# Data File Extraction
from shapely.geometry import mapping
from rioxarray.merge import merge_datasets
import rioxarray as rxr
import earthpy.plot as ep
import geopandas

# File IO
import glob

# Extract all files and merge datasets
modis_datasets = [rxr.open_rasterio(dataset, masked=True) for dataset in glob.glob(r'Global/*.hdf')]
modis_pre = merge_datasets(modis_datasets)

# Get the geometry
mexico = geopandas.read_file(r'C:\Users\Projects\Desktop\GPGN 470\Final_Project\Shape_Files\Mexico\Mexico.shp')

# Clip dataset
modis_clipped = modis_pre.rio.clip(geometries=mexico.geometry.apply(mapping), crs=4326)
modis_reproject = modis_clipped.rio.reproject('EPSG:3857')

modis_reproject.LC_Type1.plot(figsize=(15, 10))
plt.show()
