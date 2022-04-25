import os

# Project Root Directory
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Server Authentication
# TODO set auth in config to grab credentials when necessary
AUTH = {'USERNAME': 'TylerSingleton', 'PASSWORD': 'FooBar1234'}

# FTP File
# TODO this might need to be changed into a dictionary for future uses
FTP_FILES = ['gridloc.EASE2_M36km.tgz']