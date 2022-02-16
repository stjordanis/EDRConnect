import requests
import urllib
from requests import Response


class BaseUrlSession(requests.Session):
    base_url = None

    def __init__(self, base_url=None, verify_ssl=True):
        if verify_ssl and not base_url.startswith('https'):
            raise ValueError('Base URL must be HTTPS')

        self.base_url = base_url
        super(BaseUrlSession, self).__init__()

    def request(self, method, url, *args, **kwargs) -> Response:
        'Send the request after generating the complete URL.'
        url = self.create_url(url)
        return super(BaseUrlSession, self).request(
            method, url, *args, **kwargs
        )

    def prepare_request(self, request) -> Response:
        'Prepare the request after generating the complete URL.'
        request.url = self.create_url(request.url)
        return super(BaseUrlSession, self).prepare_request(request)

    def create_url(self, url) -> str:
        'Create the URL based off this partial path.'
        return urllib.parse.urljoin(self.base_url, url)
