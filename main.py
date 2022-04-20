# Tyler Singleton
# Final Project for GPGN470

# Necessary Libraries
import os
import sys

import numpy as np

# File IO
import os


# Data Extraction
class DataFileExtraction:
    def __init__(self, source_path):
        self.project_root = os.path.dirname(os.path.dirname(__file__))
        self.source_root = self.path_constructor(source_path)

    def path_constructor(self, source_path):
        if os.path.isabs(source_path):
            return source_path

        try:
            # Check path relative to root directory
            # Return absolute path or FileNotFoundError
            source_root = os.path.join(self.project_root, source_path)
            if os.path.isfile(source_path):
                return source_root
            raise FileNotFoundError("Cannot locate file from: \n{}".format(source_root))
        except FileNotFoundError as err:
            sys.exit(err)
