import os
import requests
import urllib.request
import shutil
import urllib.request as request
from contextlib import closing
from tqdm import *
from definitions import AUTH, FTP_FILES


# Class override taken from EarthData
# Overriding requests.Session.rebuild_auth to maintain headers when redirected
class SessionWithHeaderRedirection(requests.Session):
    AUTH_HOST = 'urs.earthdata.nasa.gov'

    def __init__(self, username, password):
        super().__init__()
        self.auth = (username, password)

    # Overrides from the library to keep headers when redirected to or from
    # the NASA auth host.
    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        url = prepared_request.url
        if 'Authorization' in headers:
            original_parsed = requests.utils.urlparse(response.request.url)
            redirect_parsed = requests.utils.urlparse(url)
            if (original_parsed.hostname != redirect_parsed.hostname) and \
                    redirect_parsed.hostname != self.AUTH_HOST and \
                    original_parsed.hostname != self.AUTH_HOST:
                del headers['Authorization']
        return


class ServerRequest:
    """Requesting files from the server for download

    Methods:
        __init__(self, dir_path, urls, basename)
        request(self)
    """
    def __init__(self, file_dir, urls, basename):
        self.auth = AUTH.values()
        self.urls = urls
        self.dir_path = file_dir
        self.basename = basename

        # Methods
        self.request()

    def request(self):
        """Send requests to servers"""
        print(self.basename)
        if self.basename == 'EASE-2_Grid':
            self.ftp_request()
        elif self.basename == 'CYGNSS' or self.basename == 'SMAP':
            self.earth_data_request()
        elif self.basename == 'Shape_Files':
            self.shape_file_request()
        else:
            print('Request does not exist... Yet!')

    def shape_file_request(self):
        """Default request"""
        zip_file = self.basename + '.zip'

        for url in self.urls:
            response = requests.get(url)

            # TODO Look into using tempfile package
            # Create a temporary zip file within the project root
            # Decompress into its respective directory
            with open(zip_file, 'wb') as file:
                file.write(response.content)

            shutil.unpack_archive(zip_file, self.basename)
            shutil.move(self.basename, self.dir_path)

            # Delete the temporary file
            os.remove(zip_file)

    # TODO Make this more general to accommodate other requests
    def ftp_request(self):
        """Send requests to FTP and download file"""
        cwd = os.getcwd()  # Get current directory for processing
        for url, ftp_file in list(zip(self.urls, FTP_FILES)):

            with closing(request.urlopen(os.path.join(url, ftp_file))) as response:
                with open(os.path.join(self.dir_path, ftp_file), 'wb') as file:
                    shutil.copyfileobj(response, file)

            # TODO Use absolute file path instead of relative
            # Change system path for shell command
            os.chdir(self.dir_path)

            # Unpack compressed tar file and delete file
            os.system(f'tar -xvf {ftp_file}')
            os.system(f'del {ftp_file}')

            # Change system path back to
            os.chdir(cwd)

    def earth_data_request(self):
        """Send requests to EarthData servers and download files"""
        session = SessionWithHeaderRedirection
        for url in self.urls:
            # Extract the filename from the url to be used when saving the file
            filename = url[url.rfind('/') + 1:]
            filepath = os.path.join(self.dir_path, filename)

            try:
                # Submit the request using the session
                # And raise exception HTTPError if one occurred
                response = session.get(url=url, stream=True)
                response.raise_for_status()

                # Initializes progress bar
                progress_bar = tqdm(total=int(response.headers['Content-Length']))

                # Save the data to designated file path
                with open(filepath, 'wb') as fd:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        fd.write(chunk)
                        progress_bar.update(len(chunk))

            except requests.exceptions.HTTPError as err:
                # Handle error if any were raised
                print(err)