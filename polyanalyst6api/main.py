from urllib import parse

import requests
import urllib3

from . import __version__
from .exceptions import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

__all__ = ['ClientSession', 'Project', 'PAException', 'AuthException',
           'ClientException', 'APIException']

API_PATH = '/polyanalyst/api/'
API_VERSION = 'v1.0'


class ClientSession:
    user_agent = f'PolyAnalyst6API python client v{__version__}'

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.logout()
        except NotImplementedError:
            return True

    def __init__(self, netloc, username, password):
        self.netloc = netloc
        self.usr = username
        self.pwd = password

        self._s = requests.Session()
        self.id = None  # session identity

        # path to certificate file. by default ignore insecure connection warnings
        self.certfile = False

    def login(self):
        params = {'uname': self.usr, 'pwd': self.pwd}
        resp, _ = self.request('POST', 'login', params=params)
        self.id = resp.cookies['sid']

    def logout(self):
        raise NotImplementedError()

    def project(self, uuid):
        try:
            prj = Project(self, uuid)
            _ = prj.nodes
        except PAException:
            raise
        return prj

    def request(self, method, *paths, **requests_kwargs):
        method = method.upper()
        url = self.construct_url(*paths)
        try:
            response = self._s.request(method, url, **requests_kwargs, verify=self.certfile)
        except requests.RequestException as e:
            raise ClientException(str(e))

        return self.handle_response(response)

    def handle_response(self, response):
        try:
            data = response.json()
        except ValueError:
            data = None

        if response.status_code in (200, 202):
            return response, data

        error_msg = self.get_error_details(data)

        if response.status_code == 403:
            raise AuthException('Authorization Required. You are not logged in'
                                ' to PolyAnalyst Server.')

        if 'Login failed' in error_msg:
            raise AuthException(error_msg)

        if response.status_code == 404:
            error_msg = 'Invalid API resource.'
        elif data is None:
            error_msg = 'Unable to decode JSON response.'

        raise APIException(error_msg, response.url, response.status_code)

    @staticmethod
    def get_error_details(data):
        if data and isinstance(data, list):
            msg = data[1]
        else:
            msg = 'An unknown error has occurred processing your request.'

        return msg

    def construct_url(self, *paths):
        url = parse.urljoin(self.netloc, API_PATH) + API_VERSION + '/'
        for path in paths:
            url = parse.urljoin(url, path)
        return url


class Project:
    def __init__(self, session, uuid):
        self.client_session = session
        self.id = uuid

        self._nodes = {}

    @property
    def nodes(self):
        _, json = self.client_session.request(
            'get',
            'project/', 'nodes',
            params={'prjUUID': self.id},
            headers={'sid': self.client_session.id}
        )
        for node in json['nodes']:
            node_name = node.pop('name')
            self._nodes[node_name] = node

        return self._nodes

    def save(self):
        _, _ = self.client_session.request(
            'post',
            'project/', 'save',
            json={'prjUUID': self.id}
        )

    def abort(self):
        _, _ = self.client_session.request(
            'post',
            'project/', 'global-abort',
            json={'prjUUID': self.id}
        )

    def execute(self, node):
        if node not in self.nodes:
            raise APIException(f"Node '{node}' is not found on the server")
        _, _ = self.client_session.request(
            'post',
            'project/', 'execute',
            json={
                'prjUUID': self.id,
                'nodes': [{'type': self._nodes[node]['type'], 'name': node}]
            }
        )

    def result(self, node):
        if node not in self.nodes:
            raise APIException(f"Node '{node}' is not found on the server")
        _, data = self.client_session.request(
            'get',
            'dataset/', 'preview',
            params={'prjUUID': self.id, 'name': node, 'type': self._nodes[node]['type']}
        )
        return data
