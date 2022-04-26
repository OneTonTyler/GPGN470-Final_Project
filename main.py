# Tyler Singleton
# Final Project for GPGN470

# Necessary Libraries
import sys
import matplotlib.pyplot as plt

# GeoProcessing
import json
import h5py
import geopandas
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray as rxr

from shapely.geometry import mapping, Point
from rioxarray.merge import merge_datasets

# File IO
import os
import shutil
import glob

# Custom Files
from definitions import ROOT_DIR
from server_request import ServerRequest


# NOTE I might want to reconsider how these classes are designed to function to make them more modular
class DataFileExtraction:
    """ Creates the file tree for downloading and storing data

    Methods:
        __init__(self)
        dir_constructor(self)
        data_constructor(self)
        save_data(self)
    """
    def __init__(self):
        self.project_root = ROOT_DIR
        self.data_dir = os.path.join(self.project_root, 'Data_Files')
        self.urls_dir = os.path.join(self.project_root, 'URLs')

        # Constructors
        self.dir_constructor()

    # TODO Add a function to check if the files already exist without removing and
    #   only download new files
    # NOTE may be best to remove this method to have the data_constructor create the file directories
    def dir_constructor(self):
        """Create a file directory for the data to be downloaded and stored"""
        try:
            # Create a new directory if no directory exists
            os.mkdir(self.data_dir)
            for file in ['CYGNSS', 'EASE-2_Grid', 'SMAP']:
                os.mkdir(os.path.join(self.data_dir, file))

            # Load data into files
            self.data_constructor()

        # If a directory exists, ask user if they wish to continue
        # This will remove the upper level data folder
        except FileExistsError:
            print('Directory already exists, \nContinuing will remove the current contents')
            user_input = input('Continue: Y/N \n>>> ')
            if user_input == 'Y' or user_input == 'y':
                # TODO I should be able to download files without have to remove or overwrite additional files
                shutil.rmtree(self.data_dir, ignore_errors=True)
                self.dir_constructor()

        # Something must be wrong with the root directory
        except FileNotFoundError:
            print(f'Cannot create path: {self.data_dir}')
            sys.exit(1)

    def data_constructor(self):
        """Extracts the proper data files from EarthData Search"""
        # Iterate through the text files
        for url_file in os.listdir(self.urls_dir):
            # Open text file and make a list of urls
            with open(os.path.join(self.urls_dir, url_file)) as file:
                urls = [url.strip('\n') for url in list(file)]

            # Getting the directory name from the file name
            # ...\URLs\SMAP.txt -> ...\Data_Files\SMAP
            basename = os.path.splitext(os.path.basename(url_file))[0]
            file_dir = os.path.join(self.data_dir, basename)

            print('\nDownloading files')
            ServerRequest(file_dir, urls, basename)


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


# Create directory tree and download necessary files
# DataFileExtraction()

# ------------------------------------------------
# Processing data
# Reading the geometry shapefile for masking
shape_file = r'Data_Files\Shape_Files\world-administrative-boundaries.shp'

world_boundaries = geopandas.read_file(shape_file)
mexico_mask = world_boundaries['geometry'].loc[world_boundaries['name'] == 'Mexico']

# Processing Files
save_data(r'Data_Files\SMAP\*.h5', 'SMAP', mexico_mask)
save_data(r'Data_Files\CYGNSS\*.nc', 'CYGNSS', mexico_mask)

# # ------------------------------------------------
# # TODO Save files to disk
# # TODO The following processes could be transformed into a class
# # Reading and processing SMAP files
# # Extracting the dataset into memory
# smap_files = r'Data_Files\SMAP\*.h5'
# smap = [h5py.File(dataset) for dataset in glob.glob(smap_files)]
#
# # TODO Extract the PM data as well
# # Converting dataset into a pandas dataframe object
# smap = [pd.DataFrame({
#     'Landcover_Class_0': dataset['Soil_Moisture_Retrieval_Data_AM']['landcover_class'][:, :, 0].ravel(),
#     'Landcover_Class_1': dataset['Soil_Moisture_Retrieval_Data_AM']['landcover_class'][:, :, 1].ravel(),
#     'Landcover_Class_2': dataset['Soil_Moisture_Retrieval_Data_AM']['landcover_class'][:, :, 2].ravel(),
#     'Soil_Moisture': dataset['Soil_Moisture_Retrieval_Data_AM']['soil_moisture'][:].ravel(),
#     'Latitude': dataset['Soil_Moisture_Retrieval_Data_AM']['latitude'][:].ravel(),
#     'Longitude': dataset['Soil_Moisture_Retrieval_Data_AM']['longitude'][:].ravel()
# }) for dataset in smap]
# smap = pd.concat(smap, ignore_index=True)
#
# # Setting the latitude and longitude into point coordinates
# smap['Coordinates'] = list(zip(smap.Longitude, smap.Latitude))
# smap['Coordinates'] = smap['Coordinates'].apply(Point)
#
# # Convert from Pandas Dataframe Object into a GeoPandas Dataframe Object
# # Unknown values are masked as -9999
# smap = geopandas.GeoDataFrame(smap.query('Soil_Moisture >= 0'), geometry='Coordinates')
# smap = smap.set_crs('epsg:4326')
# smap = smap.drop_duplicates(subset='Coordinates')
#
# # Clip Geopandas Dataframe with our mexico_mask
# smap = geopandas.clip(smap, mexico_mask)
# smap = smap.reset_index(drop=True)
#
# # ------------------------------------------------
# # Reading and processing CYGNSS files
# # Extracting the dataset into memory using xarray for reading netcdf4
# cygnss_files = r'Data_Files\CYGNSS\*.nc'
# cygnss = [xr.open_dataset(dataset) for dataset in glob.glob(cygnss_files)]
#
# # Convert into a Pandas DataFrame Object
# # Longitude values go from 0 to 360, so 180 can be subtracted
# cygnss = [pd.DataFrame({
#     'SNR': dataset['ddm_snr'].values.ravel(),
#     'Latitude': dataset['sp_lat'].values.ravel(),
#     'Longitude': dataset['sp_lon'].values.ravel() - 180
# }) for dataset in cygnss]
# cygnss = pd.concat(cygnss, ignore_index=True)
#
# # Setting the latitude and longitude into point coordinates
# cygnss['Coordinates'] = list(zip(cygnss.Longitude, cygnss.Latitude))
# cygnss['Coordinates'] = cygnss['Coordinates'].apply(Point)
#
# # Convert from Pandas Dataframe Object into a GeoPandas Dataframe Object
# cygnss = geopandas.GeoDataFrame(cygnss, geometry='Coordinates')
# cygnss = cygnss.set_crs('epsg:4326')
#
# # Clip Geopandas Dataframe with our mexico_mask
# cygnss = geopandas.clip(cygnss, mexico_mask)
#
# # ------------------------------------------------
