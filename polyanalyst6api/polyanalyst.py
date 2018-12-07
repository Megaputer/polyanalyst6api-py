from urllib.parse import urljoin
from typing import Dict, List, Tuple, Union

import requests

from . import __version__
from .exceptions import *

__all__ = ['API', 'Project', 'PAException', 'ClientException', 'APIException']

_API_PATH = '/polyanalyst/api/'
_VALID_API_VERSIONS = ['1.0']

# typing
_Response = Tuple[requests.Response, any]
_Nodes = Dict[str, Dict[str, Union[int, str]]]
_DataSet = List[Dict[str, any]]


class API:
    """A client for the PolyAnalyst API.

    :param url: The scheme, host and port(if exists) of a PolyAnalyst server
    :param username: The username to login with
    :param password: (optional) The password for specified username
    :param version: API version to use (ex. '1.0' etc.)

    Usage::

      >>> import polyanalyst6api
      >>> api = polyanalyst6api.API(URL, USERNAME, PASSWORD)
      >>> api.login()

      >>> with polyanalyst6api.API(URL, USERNAME, PASSWORD) as api:
      >>>     pass
    """

    user_agent = f'PolyAnalyst6API python client v{__version__}'

    def __enter__(self) -> 'API':
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._s.__exit__()

    def __init__(
        self,
        url: str,
        username: str,
        password: str = '',
        version: str = '1.0',
    ) -> None:
        if version not in _VALID_API_VERSIONS:
            raise ClientException('Valid api versions are ' + ', '.join(_VALID_API_VERSIONS))

        self.base_url = f'{urljoin(url, _API_PATH)}v{version}/'
        self.username = username
        self.password = password

        self._s = requests.Session()
        self.sid = ''  # session identity
        # path to certificate file. by default ignore insecure connection warnings
        self.certfile = False

    def login(self) -> None:
        """Log in to PolyAnalyst Server."""
        resp, _ = self.request(
            'login',
            method='post',
            params={'uname': self.username, 'pwd': self.password},
        )
        self.sid = resp.cookies['sid']

    def run_task(self, id: int) -> None:
        """Initiate scheduler task execution."""
        self.post('scheduler/run-task', json={'taskId': id})

    def project(self, uuid: str) -> 'Project':
        """Check project with given uuid on existence and return project instance"""
        prj = Project(self, uuid)
        _ = prj.nodes
        return prj

    def get(self, endpoint: str, **kwargs):
        """Shortcut for GET requests via :class:`request`"""
        return self.request(endpoint, method='get', **kwargs)[1]

    def post(self, endpoint: str, **kwargs):
        """Shortcut for POST requests via :class:`request`"""
        return self.request(endpoint, method='post', **kwargs)[1]

    def request(self, endpoint: str, method: str, **kwargs) -> _Response:
        url = urljoin(self.base_url, endpoint)
        kwargs['verify'] = self.certfile
        try:
            resp = self._s.request(method, url, **kwargs)
        except requests.RequestException as e:
            raise ClientException(e)

        return self._handle_response(resp)

    @staticmethod
    def _handle_response(response: requests.Response) -> _Response:
        try:
            json = response.json()
        except ValueError:
            json = None

        if response.status_code in (200, 202):
            return response, json

        if response.status_code == 403:
            raise APIException(
                'You are not logged in to PolyAnalyst Server or'
                'Access to this operation is limited to project owners and administrator',
                response.url,
                403,
            )

        if response.status_code == 500:
            try:
                if json[0] != 'Error':
                    raise Exception
                error_msg = json[1]
            except Exception:
                pass
            else:
                raise APIException(error_msg, response.url, response.status_code)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise APIException(e, response.url, response.status_code)

        raise ClientException('An error occurred processing your request')


class Project:
    """The class maintains all operations with the PolyAnalyst's project and nodes.

    :param api An instance of API class
    :param uuid The uuid of the project you want to interact with
    """
    def __init__(self, api: API, uuid: str) -> None:
        self.api = api
        self.uuid = uuid
        self._nodes: _Nodes = {}

    @property
    def nodes(self) -> _Nodes:
        """Returns a dictionary of project's nodes information.

        Usage:
        >>> from polyanalyst6api import API
        >>> print(API('administrator').project(UUID).nodes)
        {'Python': {'id': 1, 'type': 'DataSource', 'status': 'empty'}}

        Every node value is a dict with a mandatory keys: id, type, status.
        It also may contain errMsg key if last node execution was failed.
        """
        json = self.api.get(
            'project/nodes',
            params={'prjUUID': self.uuid},
            headers={'sid': self.api.sid},
        )
        self._nodes = {node.pop('name'): node for node in json['nodes']}
        return self._nodes

    @property
    def execution_statistics(self) -> Tuple[_Nodes, Dict[str, int]]:
        """Returns the execution statistics for nodes in the project.

        It's similar to
        """
        json = self.api.get(
            'project/execution-statistics',
            params={'prjUUID': self.uuid}
        )
        nodes = {node.pop('name'): node for node in json['nodes']}
        return nodes, json['nodesStatistics']

    def save(self) -> None:
        """Initiates """
        self.api.post('project/save', json={'prjUUID': self.uuid})

    def abort(self) -> None:
        self.api.post('project/global-abort', json={'prjUUID': self.uuid})

    def execute(self, *node_name: str) -> None:
        """Execute nodes and their children within project."""
        self.api.post(
            'project/execute',
            json={
                'prjUUID': self.uuid,
                'nodes': [{'type': self._nodes[name]['type'], 'name': name} for name in node_name],
            },
        )

    def preview(self, node_name: str) -> _DataSet:
        return self.api.get(
            'dataset/preview',
            params={
                'prjUUID': self.uuid,
                'name': node_name,
                'type': self._nodes[node_name]['type'],
            },
        )

    def unload(self) -> None:
        """Unload the project from the memory and free system resources."""
        self.api.post('project/unload', json={'prjUUID': self.uuid})

    def repair(self) -> None:
        """Send 'repair the project' command to server."""
        self.api.post('project/repair', json={'prjUUID': self.uuid})

    def delete(self, force_unload: bool = False) -> None:
        """Delete the project from server.

        By default the project will be deleted only if it's not loaded to memory.
        To delete the project that loaded to memory (there are users working on
        this project right now) set force_unload to True.
        This operation available only for project owner and administrators and
        can not be undone.
        """
        self.api.post(
            'project/delete',
            json={'prjUUID': self.uuid, 'forceUnload': force_unload}
        )

    def __repr__(self):
        return f'<Project({self.uuid})>'
