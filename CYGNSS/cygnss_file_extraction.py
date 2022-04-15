# Data File Extraction
from shapely.geometry import mapping, Point

import matplotlib.pyplot as plt
import pandas as pd
import geopandas
import xarray as xr
import rioxarray as rxr

with xr.open_dataset(r'Global\cyg01.ddmi.s20190302-000000-e20190302-235959.l1.power-brcs.a31.d32.nc', decode_coords='all') as dataset:

    # Extract necessary values
    df = pd.DataFrame({'SNR': dataset['ddm_snr'].values.ravel(),
                       'Latitude': dataset['sp_lat'].values.ravel(),
                       'Longitude': dataset['sp_lon'].values.ravel() - 180})
    df['Coordinates'] = list(zip(df.Longitude, df.Latitude))
    df['Coordinates'] = df['Coordinates'].apply(Point)

    # Convert panda dataframe into geopandas
    gdf = geopandas.GeoDataFrame(df, geometry='Coordinates')
    gdf = gdf.set_crs('epsg:4326')

    # Clip with respect to Mexico
    mask = geopandas.read_file(r'C:\Users\Projects\Desktop\GPGN 470\Final_Project\Shape_Files\Mexico\Mexico.shp')
    gdf_clipped = geopandas.clip(gdf, mask)

    # plot
    gdf_clipped.plot('SNR', cmap='viridis', markersize=0.1)
    plt.show()