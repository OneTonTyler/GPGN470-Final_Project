# Data File Extraction
from shapely.geometry import mapping
from rioxarray.merge import merge_datasets

import rioxarray as rxr
import geopandas

# File IO
import glob


class Build_MODIS_Dataset:
    """ This class is used to return a MODIS dataset from a shapefile

    Methods:
        __init__(self, dir_modis, dir_shp, crs)
        dataset_constructor(self)
        dataset_merged(self)
        dataset_clipped(self)
    """
    def __init__(self, dir_modis, dir_shp, crs):
        self.source_path = dir_modis
        self.shapefile_path = dir_shp
        self.crs = crs
        self.dataset = self.dataset_clipped()

    def dataset_constructor(self):
        """Returns an array of xarray datasets"""
        return [rxr.open_rasterio(dataset, masked=True) for dataset in glob.glob(self.source_path + '/*.hdf')]

    def dataset_merged(self):
        """Merges xarray datasets into a single dataset - crs is assumed to be the same"""
        return merge_datasets(self.dataset_constructor())

    def dataset_clipped(self):
        """Returns a xarray dataset clipped based on its respective shapefile"""
        # Geometry must be in the form of a dict
        # Cannot use geopandas dataframe
        geometries = geopandas.read_file(self.shapefile_path).geometry.apply(mapping)
        return self.dataset_merged().rio.clip(geometries=geometries, crs=self.crs)