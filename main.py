# Tyler Singleton
# Final Project for GPGN470
##
# Viewing
import matplotlib.pyplot as plt

# Machine Learning
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn import svm

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
##

def save_data(path, file_type, mask):
    """Save the files to disk"""
    # Extract datasets
    if file_type == 'SMAP':
        # Extracting dataset
        datasets = [h5py.File(dataset) for dataset in glob.glob(path)]

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
    cygnss_gdf = geopandas.read_file(r'CYGNSS\CYGNSS.shp').drop(columns=['Latitude', 'Longitude'])
    smap_gdf = geopandas.read_file(r'SMAP\SMAP.shp').drop(columns=['Latitude', 'Longitude'])
    ease2_gdf = geopandas.read_file(r'EASE2\EASE2.shp').drop(columns=['Latitude', 'Longitude'])

    gdf = geopandas.sjoin_nearest(ease2_gdf, cygnss_gdf).drop(columns='index_right')
    gdf = geopandas.sjoin_nearest(gdf, smap_gdf).drop(columns='index_right')
    gdf = gdf.reset_index()

    if not os.path.isdir('Master'):
        os.mkdir('Master')

    gdf.to_file(r'Master\Master.shp')

# ------------------------------------------------
## Machine learning
gdf = geopandas.read_file(r'Data_Files\Shape_Files\Master\Master.shp')

dataframe = pd.DataFrame(gdf.drop(columns='geometry')).dropna()
dataset = np.array([dataframe[col].values for col in dataframe.columns])

X = dataset[:-1].T
y = dataset[-1:].T

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33)

# Decision Tree Regression
# Fit regression model
regression = DecisionTreeRegressor(max_depth=5)
regression.fit(X_train, y_train)

# Predict
y_pred_tree = regression.predict(X_test)

# Neural Networks
scaler = StandardScaler()
scaler.fit(X_train)

X_train = scaler.transform(X_train)
X_test = scaler.transform(X_test)

regression_neural = MLPRegressor(max_iter=2000)
regression_neural.fit(X_train, y_train)

y_pred_neural = regression_neural.predict(X_test)

# Support Vector Machine
regression_svm = svm.SVR()
regression_svm.fit(X_train, y_train)

y_pred_svm = regression_svm.predict(X_test)

# Error
rmse_tree = np.sqrt(mean_squared_error(y_test, y_pred_tree))
r2_tree = r2_score(y_test, y_pred_tree)

rmse_neural = np.sqrt(mean_squared_error(y_test, y_pred_neural))
r2_neural = r2_score(y_test, y_pred_neural)

rmse_svm = np.sqrt(mean_squared_error(y_test, y_pred_svm))
r2_svm = r2_score(y_test, y_pred_svm)


print(f'Error: rmse {rmse_tree}, r2 {r2_tree}')
print(f'Error: rmse {rmse_neural}, r2 {r2_neural}')
print(f'Error: rmse {rmse_svm}, r2 {r2_svm}')

# ------------------------------------------------
## Plotting the results
with ChangeDirectory(r'Data_Files\Shape_Files'):
    gdf_smap = geopandas.read_file(r'SMAP\SMAP.shp')
    gdf_pred = geopandas.read_file(r'Master\Master.shp').dropna()

gdf_pred['Decision_Tree'] = regression.predict(X)
gdf_pred['Neural_Network'] = regression_neural.predict(scaler.transform(X))
gdf_pred['Support_Vector'] = regression_svm.predict(scaler.transform(X))

gdf_smap.plot('Soil_Moist', markersize=20)
plt.show()

gdf_pred.plot('Decision_Tree', markersize=20)
plt.show()

gdf_pred.plot('Neural_Network', markersize=20)
plt.show()

gdf_pred.plot('Support_Vector', markersize=20)
plt.show()
