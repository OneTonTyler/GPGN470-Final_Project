# Tyler Singleton
# Final Project for GPGN470

# Necessary Libraries

# GeoProcessing
import h5py
import geopandas
import numpy as np
import pandas as pd
import xarray as xr

from shapely.geometry import Point

# File IO
import os
import shutil
import glob

# Custom Files
from server_request import DatasetDownloadRequest, ChangeDirectory


def save_data(path, file_type, mask):
    """Save the files to disk"""
    # Extract datasets
    if file_type == 'SMAP':
        # Extracting dataset
        datasets = [h5py.File(dataset) for dataset in glob.glob(path)]

        # TODO: Figure out how to pass this in as an argument
        # Convert datasets into pandas dataframe object
        df = [pd.DataFrame({
            'Landcover_Class_0': dataset['Soil_Moisture_Retrieval_Data_AM']['landcover_class'][:, :, 0].ravel(),
            'Landcover_Class_1': dataset['Soil_Moisture_Retrieval_Data_AM']['landcover_class'][:, :, 1].ravel(),
            'Landcover_Class_2': dataset['Soil_Moisture_Retrieval_Data_AM']['landcover_class'][:, :, 2].ravel(),
            'Soil_Moisture': dataset['Soil_Moisture_Retrieval_Data_AM']['soil_moisture'][:].ravel(),
            'Latitude': dataset['Soil_Moisture_Retrieval_Data_AM']['latitude'][:].ravel(),
            'Longitude': dataset['Soil_Moisture_Retrieval_Data_AM']['longitude'][:].ravel()
        }) for dataset in datasets]
        df = pd.concat(df, ignore_index=True)

    elif file_type == 'CYGNSS':
        # Extracting the dataset into memory using xarray for reading netcdf4
        datasets = [xr.open_dataset(dataset) for dataset in glob.glob(path)]

        # Convert into a Pandas DataFrame Object
        # Longitude values go from 0 to 360, so 180 can be subtracted
        df = [pd.DataFrame({
            'SNR': dataset['ddm_snr'].values.ravel(),
            'Latitude': dataset['sp_lat'].values.ravel(),
            'Longitude': dataset['sp_lon'].values.ravel() - 180
        }) for dataset in datasets]
        df = pd.concat(df, ignore_index=True)

    elif file_type == 'EASE2':
        datasets = [np.fromfile(dataset, dtype=np.float64) for dataset in glob.glob(path)]
        df = pd.DataFrame({
            'Latitude': datasets[0],
            'Longitude': datasets[1]
        })
    # Setting the latitude and longitude into point coordinates
    # Must have a latitude and longitude pair
    df['Coordinates'] = list(zip(df.Longitude, df.Latitude))
    df['Coordinates'] = df['Coordinates'].apply(Point)


    # Convert from Pandas Dataframe Object into a GeoPandas Dataframe Object
    # Unknown values are masked as -9999
    if file_type == 'SMAP':
        gdf = geopandas.GeoDataFrame(df.query('Soil_Moisture >= 0'), geometry='Coordinates')
    else:
        gdf = geopandas.GeoDataFrame(df, geometry='Coordinates')

    gdf = gdf.set_crs('epsg:4326')
    gdf = gdf.drop_duplicates(subset='Coordinates')

    # Clip Geopandas Dataframe with our mexico_mask
    gdf = geopandas.clip(gdf, mask)
    gdf = gdf.reset_index(drop=True)

    # Save data geodataframe object to file
    base_dir = os.path.join(r'Data_Files\Shape_Files', file_type)
    if not os.path.exists(base_dir):
        os.mkdir(base_dir)

    gdf.to_file(os.path.join(base_dir, file_type + '.shp'))


# ------------------------------------------------
# Create directory tree and download necessary files
request = DatasetDownloadRequest()

# Getting Urls
files = os.listdir('URLs')  # CYGNSS, EASE-2_Grid, Shape_Files, SMAP
print(files)

urls = [[url.strip('\n') for url in list(open(os.path.join('URLs', file)))] for file in files]

# Downloading the files
with ChangeDirectory('Data_Files'):
    request.server_request(urls[0], 'CYGNSS', host='urs.earthdata.nasa.gov', stream=True)
    request.server_request(urls[1], 'EASE-2_Grid')
    request.server_request(urls[2], r'Shape_Files\Mexico')
    request.server_request(urls[3], 'SMAP', host='urs.earthdata.nasa.gov', stream=True)

# Unpacking zip file
print('Unpacking Files...')
with ChangeDirectory(r'Data_Files\Shape_Files\Mexico'):
    shutil.unpack_archive('world-administrative-boundaries.zip')
    os.remove('world-administrative-boundaries.zip')

# Unpacking compressed tar file
with ChangeDirectory(r'Data_Files\EASE-2_Grid'):
    os.system(f'tar -xvf gridloc.EASE2_M36km.tgz')
    os.system(f'del gridloc.EASE2_M36km.tgz')


# ------------------------------------------------
# Processing data
# Reading the geometry shapefile for masking
print('Processing shape files...')
shape_file = r'Data_Files\Shape_Files\Mexico\world-administrative-boundaries.shp'

world_boundaries = geopandas.read_file(shape_file)
mexico_mask = world_boundaries['geometry'].loc[world_boundaries['name'] == 'Mexico']

# Processing Files
save_data(r'Data_Files\SMAP\*.h5', 'SMAP', mexico_mask)
save_data(r'Data_Files\CYGNSS\*.nc', 'CYGNSS', mexico_mask)
save_data(r'Data_Files\EASE-2_Grid\*', 'EASE2', mexico_mask)

# ------------------------------------------------
# Join our shape files into a single geopanda dataframe object
print('Merging shape files...')
with ChangeDirectory(r'Data_Files\Shape_Files'):
    cygnss_gdf = geopandas.read_file(r'CYGNSS\CYGNSS.shp')
    smap_gdf = geopandas.read_file(r'SMAP\SMAP.shp')
    ease2_gdf = geopandas.read_file(r'EASE2\EASE2.shp')

    gdf = geopandas.sjoin_nearest(ease2_gdf, cygnss_gdf)
    gdf = geopandas.sjoin_nearest(ease2_gdf, smap_gdf)
    gdf = gdf.drop(columns=['Latitude_left', 'Longitude_left', 'Latitude_right', 'Longitude_right', 'index_right'])
    gdf = gdf.reset_index()

    if not os.path.isdir('Master'):
        os.mkdir('Master')

    gdf.to_file(r'Master\Master.shp')

# ------------------------------------------------
# Machine learning

print('Done!')
