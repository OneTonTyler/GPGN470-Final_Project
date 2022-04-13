import geopandas
import os


class Build_ShapeFile:
    """ ShapeFile class is used to generate a shapefile library for future use

    Methods:
        __init__(self, name)
        __repr__(self)
        shapefile_constructor(self)
    """

    def __init__(self, name):
        self.source_path = r'Shape_Files/Global/countries.shp'
        self.path = r'Shape_Files/{name}'.format(name=name)
        self.shp = self.path + r'/{name}.shp'.format(name=name)
        self.name = name

        self.shapefile_constructor()

    def shapefile_constructor(self):
        """Generate a basemap from existing shapefile"""
        # Check if directory exists
        if not os.path.isdir(self.path):
            os.mkdir(self.path)

        try:
            # Create GeoDataFrame from Source
            world = geopandas.read_file(self.source_path)
            # Extract GeoSeries and save as ShapeFile
            world.loc[world['COUNTRY'] == self.name].to_file(self.path)
        except Exception as err:
            print(err)
            pass

    def geo_dataframe(self):
        """Return the GeoDataFrame"""
        return geopandas.read_file(self.shp)
