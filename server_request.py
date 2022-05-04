# Necessary Imports
import re
import os
import shutil
import requests
import urllib.request as request

from requests.exceptions import HTTPError, InvalidSchema
from contextlib import closing

# Progress bar
from tqdm import tqdm

# Custom files
from definitions import AUTH, ROOT_DIR


class SessionWithHeaderRedirection(requests.Session):
    """Session override was provided by EarthData"""
    AUTH_HOST = None

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


class ChangeDirectory:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


class BaseAuthenticator:
    """Parent class for server authentication

    Methods:
        __init__(self)
    """
    def __init__(self):
        self.username = AUTH['USERNAME']
        self.password = AUTH['PASSWORD']


class DatasetDownloadRequest(BaseAuthenticator):
    """
    Gets a response from the server. If status code is 200, retrieve and download the contents.
    Else, return an exception.

    Methods:
        __init__(self)
        server_request(self, urls, path, host, **kwargs)
        server_download(response)
        ftp_server_download(response)
        scan_directory(path)
    """
    def __init__(self):
        super().__init__()
        self.root = ROOT_DIR

    def server_request(self, urls, path, host=None, **kwargs):
        """Sends request using the request package"""
        print('Connecting to server...')

        # Create session
        if host:
            session = SessionWithHeaderRedirection(self.username, self.password)
            session.AUTH_HOST = host
        else:
            session = requests.Session()

        # Scan the directory for files
        self.scan_directory(path)

        # Iterate through urls
        with ChangeDirectory(path):
            for url in urls:
                try:
                    # Raise HTTPError exception if auth fails
                    response = session.get(url, **kwargs)
                    response.raise_for_status()

                    # Download data
                    self.server_download(response, url)
                    session.close()

                except HTTPError:
                    print('Authentication failed.')

                # Since requests does not support FTP links
                # NOTE The file path is hardcoded for now.
                #   Need to reconfigure to allow a set of file paths.
                except InvalidSchema:
                    ftp_path = os.path.join(url, 'gridloc.EASE2_M36km.tgz')
                    if not os.path.isfile(ftp_path):
                        with closing(request.urlopen(ftp_path)) as response:
                            self.ftp_server_download(response)

        print('Done!')

    @staticmethod
    def scan_directory(path):
        """Checks if a directory exists, and returns a list of files not found in the directory"""
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
            except Exception as e:
                print(e)

    @staticmethod
    def server_download(response, url=None):
        """Download file from server"""

        # Check if the headers contain a filename
        # Else use the file url as the filename
        regex = re.compile(r'(?<=filename=")[\w.-]+')

        try:
            filename = regex.search(response.headers['content-disposition'])[0]
        except (TypeError, KeyError):
            filename = url[url.rfind('/') + 1:]

        # Extract contents from response object and save onto disk
        if not os.path.isfile(filename):
            # Initialize progress bar
            progress_bar = tqdm(total=int(response.headers['Content-Length']))

            with open(filename, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)
                    progress_bar.update(len(chunk))

    @staticmethod
    def ftp_server_download(response):
        with open('gridloc.EASE2_M36km.tgz', 'wb') as file:
            shutil.copyfileobj(response, file)
