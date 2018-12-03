import urllib.parse
from typing import Dict, List, Tuple, Union

import requests

from . import __version__
from .exceptions import *

__all__ = [
    'ClientSession',
    'Project',
    'PAException',
    'AuthException',
    'ClientException',
    'APIException',
]

API_PATH = '/polyanalyst/api/'
API_VERSION = 'v1.0'

# typing
_Nodes = Dict[str, Dict[str, Union[int, str]]]
_Response = Tuple[requests.Response, any]
_Json = List[Dict[str, any]]


class ClientSession:
    user_agent = f'PolyAnalyst6API python client v{__version__}'

    def __enter__(self) -> 'ClientSession':
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __init__(self, netloc: str, username: str, password: str) -> None:
        self.netloc = netloc
        self.username = username
        self.password = password

        self._s = requests.Session()
        self.id = ''  # session identity

        # path to certificate file. by default ignore insecure connection warnings
        self.certfile = False

    def login(self) -> None:
        resp, _ = self.request(
            '/login', 'post', params={'uname': self.username, 'pwd': self.password}
        )
        self.id = resp.cookies['sid']

    def project(self, uuid: str) -> 'Project':
        try:
            prj = Project(self, uuid)
            _ = prj.nodes
        except PAException:
            raise
        return prj

    def request(self, path: str, method: str = 'get', **kwargs) -> _Response:
        url = self.construct_url(path)
        kwargs['verify'] = self.certfile
        try:
            response = self._s.request(method, url, **kwargs)
        except requests.RequestException as e:
            raise ClientException(str(e))

        return self.handle_response(response)

    def handle_response(self, response: requests.Response) -> _Response:
        try:
            data = response.json()
        except ValueError:
            data = None

        if response.status_code in (200, 202):
            return response, data

        error_msg = self.get_error_details(data)

        if response.status_code == 403:
            raise AuthException(
                'Authorization Required. You are not logged in to PolyAnalyst Server.'
            )

        if 'Login failed' in error_msg:
            raise AuthException(error_msg)

        if response.status_code == 404:
            error_msg = 'Invalid API resource.'
        elif data is None:
            error_msg = 'Unable to decode JSON response.'

        raise APIException(error_msg, response.url, response.status_code)

    @staticmethod
    def get_error_details(data: Union[List[str], any]) -> str:
        if data and isinstance(data, list):
            msg = data[1]
        else:
            msg = 'An unknown error has occurred processing your request.'

        return msg

    def construct_url(self, path: str) -> str:
        return urllib.parse.urljoin(self.netloc, API_PATH) + API_VERSION + path


class Project:
    def __init__(self, session: ClientSession, uuid: str) -> None:
        self.client_session = session
        self.id = uuid

        self._nodes: _Nodes = {}

    @property
    def nodes(self) -> _Nodes:
        json: Dict[str, _Json]
        _, json = self.client_session.request(
            '/project/nodes',
            params={'prjUUID': self.id},
            headers={'sid': self.client_session.id},
        )
        for node in json['nodes']:
            node_name = node.pop('name')
            self._nodes[node_name] = node

        return self._nodes

    def save(self) -> None:
        _, _ = self.client_session.request(
            '/project/save', 'post', json={'prjUUID': self.id}
        )

    def abort(self) -> None:
        _, _ = self.client_session.request(
            '/project/global-abort', 'post', json={'prjUUID': self.id}
        )

    def execute(self, node: str) -> None:
        if node not in self.nodes:
            raise APIException(f"Node '{node}' is not found on the server")
        _, _ = self.client_session.request(
            '/project/execute',
            'post',
            json={
                'prjUUID': self.id,
                'nodes': [{'type': self._nodes[node]['type'], 'name': node}],
            },
        )

    def result(self, node: str) -> _Json:
        if node not in self.nodes:
            raise APIException(f"Node '{node}' is not found on the server")
        json: _Json
        _, json = self.client_session.request(
            '/dataset/preview',
            params={
                'prjUUID': self.id,
                'name': node,
                'type': self._nodes[node]['type'],
            },
        )
        return json

    @property
    def statistics(self) -> Dict[str, Union[List[Dict[str, any]], Dict[str, int]]]:
        """ Retrieve the execution statistics for nodes in project.

        A readonly property.
        """
        _, json = self.client_session.request(
            '/project/execution-statistics',
            params={'prjUUID': self.id},
        )
        return json

    def unload(self) -> None:
        """ Unload the project from the memory and free system resources.

        This operation available only for project owner and administrators.
        """
        _, _ = self.client_session.request(
            '/project/unload',
            'post',
            json={'prjUUID': self.id},
        )

    def repair(self) -> None:
        """ Send 'repair the project' command to server.

        This operation available only for project owner and administrators.
        """
        _, _ = self.client_session.request(
            '/project/repair',
            'post',
            json={'prjUUID': self.id},
        )

    def delete(self, force_unload: bool = False) -> None:
        """ Remove the project from server.

        By default the project will be deleted only if it's not loaded to memory.
        To delete the project that loaded to memory (there are users working on
        this project right now) set force_unload to True.
        This operation available only for project owner and administrators and
        can not be undone.
        """
        _, _ = self.client_session.request(
            '/project/delete',
            'post',
            json={
                'prjUUID': self.id,
                'forceUnload': force_unload,
            },
        )
