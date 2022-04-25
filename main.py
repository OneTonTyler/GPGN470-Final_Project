# Tyler Singleton
# Final Project for GPGN470

# Necessary Libraries
import glob
import os
import sys

import numpy as np

# File IO
import os
import shutil

import glob
import xarray as xr

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
        except FileExistsError as err:
            print('Directory already exists, \nContinuing will remove the current contents')
            user_input = input('Continue: Y/N \n>>> ')
            if user_input == 'Y' or user_input == 'y':
                # TODO I should be able to download files without have to remove or overwrite additional files
                shutil.rmtree(self.data_dir, ignore_errors=True)
                self.dir_constructor()

        # Something must be wrong with the root directory
        except FileNotFoundError as err:
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


DataFileExtraction()

# Data Extraction
# class DataFileExtraction:
#     def __init__(self, source_path):
#         self.project_root = os.path.dirname(os.path.dirname(__file__))
#         self.source_root = self.path_constructor(source_path)
#
#     def path_constructor(self, source_path):
#         if os.path.isabs(source_path):
#             return source_path
#
#         try:
#             # Check path relative to root directory
#             # Return absolute path or FileNotFoundError
#             source_root = os.path.join(self.project_root, source_path)
#             if os.path.isdir(source_path):
#                 return source_root
#             raise FileNotFoundError("Cannot locate directory: \n{}".format(source_root))
#         except FileNotFoundError as err:
#             sys.exit(err)

    # def data_constructor(self):
    #     match os.path.splitext(self.source_root)[1]:
    #         case '.nc':
    #             dataset = [xr.open_dataset(dataset) for dataset in glob.glob()]
