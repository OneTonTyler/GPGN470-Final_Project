import os
import requests
from tqdm import *


# overriding requests.Session.rebuild_auth to maintain headers when redirected
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


# create session with the user credentials that will be used to authenticate access to the data
username = "TylerSingleton"
password = "FooBar1234"
session = SessionWithHeaderRedirection(username, password)

# the url of the file we wish to retrieve
# and remove newline character from end of urls
with open('test.txt') as url_file:
    urls = [url.strip('\n') for url in list(url_file)]

for url in urls:
    # extract the filename from the url to be used when saving the file
    filename = url[url.rfind('/') + 1:]
    filepath = os.path.join('test/', filename)

    try:
        # submit the request using the session
        response = session.get(url, stream=True)
        # raise an exception in case of http errors
        response.raise_for_status()
        # add progressbar to view file download status
        progressbar = tqdm(total=int(response.headers['Content-Length']))

        # save file
        with open(filepath, 'wb') as fd:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                fd.write(chunk)
                progressbar.update(len(chunk))

    except requests.exceptions.HTTPError as e:
        # handle any errors here
        print(e)
