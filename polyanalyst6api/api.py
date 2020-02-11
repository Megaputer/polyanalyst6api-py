"""
polyanalyst6api.api
~~~~~~~~~~~~~~~~~~~

This module contains functionality for access to PolyAnalyst API.
"""

import contextlib
import datetime
import os
import pathlib
import time
import warnings
from typing import Any, Dict, List, Tuple, Union, Optional, IO
from urllib.parse import urljoin, urlparse

import pytus
from pytus.main import _get_offset, _get_file_size
import requests
import urllib3

from . import __version__
from .exceptions import *

__all__ = ['API', 'Project', 'PAException', 'ClientException', 'APIException']

# type hints
Response = Tuple[requests.Response, Any]
Nodes = Dict[str, Dict[str, Union[int, str]]]
DataSet = List[Dict[str, Any]]

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

warnings.simplefilter('always', UserWarning)  # without this set_parameters will show warnings only once

NodeTypes = [
    "CSV Exporter/",
    "DataSource/CSV",
    "DataSource/EXCEL",
    "DataSource/FILES",
    "DataSource/INET",
    "DataSource/ODBC",
    "DataSource/RSS",
    "DataSource/XML",
    "Dataset/Biased",
    "Dataset/ExtractTerms",
    "Dataset/Python",
    "Dataset/R",
    "Dataset/ReplaceTerms",
    "ODBC Exporter/",
    "PA6TaxonomyResult/TaxonomyResult",
    "SRLRuleSet/Filter Rows",
    "SRLRuleSet/SRL Rule",
    "TmlEntityExtractor/FEX",
    "Sentiment Analysis",
    "TmlLinkTerms/",
]


class API:
    """PolyAnalyst API

    :param url: The scheme, host and port(if exists) of a PolyAnalyst server
        (e.g. ``https://localhost:5043/``, ``http://example.polyanalyst.com`` .etc)
    :param username: The username to login with
    :param password: (optional) The password for specified username
    :param ldap_server: LDAP Server address
    :param version: (optional) Choose which PolyAnalyst API version to use.
        Default: ``1.0``

    If ldap_server is provided, then login will be performed via LDAP Server.

    Usage::

      >>> import polyanalyst6api
      >>> api = polyanalyst6api.API(URL, USERNAME, PASSWORD)
      >>> api.login()

    Or as a context manager::

      >>> with polyanalyst6api.API(URL, USERNAME, PASSWORD) as api:
      >>>     ...
    """

    _api_path = '/polyanalyst/api/'
    _valid_api_versions = ['1.0']
    user_agent = f'PolyAnalyst6API python client v{__version__}'

    def __enter__(self) -> 'API':
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.logout()
        except APIException as exc:
            if exc.status_code == 404:
                pass
            else:
                raise
        self._s.__exit__()

    def __init__(
        self,
        url: str,
        username: str,
        password: str = '',
        ldap_server: Optional[str] = None,
        version: str = '1.0',
    ) -> None:
        if version not in self._valid_api_versions:
            raise ClientException('Valid api versions are ' + ', '.join(self._valid_api_versions))

        if not url:
            raise ClientException(f'Invalid url: "{url}".')

        self.base_url = urljoin(url, self._api_path)
        self.url = urljoin(self.base_url, f'v{version}/')
        self.username = username
        self.password = password
        self.ldap_server = ldap_server

        self.fs = RemoteFileSystem(self)

        self._s = requests.Session()
        self._s.headers.update({'User-Agent': self.user_agent})
        self.sid = ''  # session identity
        # path to certificate file. by default ignore insecure connection warnings
        self.certfile = False

    def get_versions(self) -> List[str]:
        """Returns api versions supported by PolyAnalyst server."""
        # the 'versions' endpoint was added in the 2191 polyanalyst's version
        try:
            return self.request(urljoin(self.base_url, 'versions'), 'get')[1]
        except APIException:
            return ['1.0']

    def get_server_info(self) -> Optional[Dict[str, Union[int, str, Dict[str, str]]]]:
        """
        Returns build, server version, and the most recent commits git hash sum
        for each repository.
        """
        _, data = self.request(urljoin(self.url, 'server/info'), 'get')
        return data

    def get_parameters(self) -> List[Dict[str, Union[str, List]]]:
        """Returns list of nodes with parameters supported by ``Parameters`` node."""
        return self.get('parameters/nodes')

    def login(self) -> None:
        """Logs in to PolyAnalyst Server with user credentials."""
        credentials = {'uname': self.username, 'pwd': self.password}
        if self.ldap_server:
            credentials['useLDAP'] = 1
            credentials['svr'] = self.ldap_server

        resp, _ = self.request(
            'login',
            method='post',
            params=credentials,
        )
        self.sid = resp.cookies['sid']

    def logout(self) -> None:
        """Logs out current user from PolyAnalyst Server."""
        self.get('logout')

    def run_task(self, id: int) -> None:
        """Initiates scheduler task execution.

        :param id: the task ID
        """
        self.post('scheduler/run-task', json={'taskId': id})

    def project(self, uuid: str) -> 'Project':
        """Checks project with given uuid on existence and returns
        :class:`Project <Project>` instance.

        :param uuid: The project uuid
        """
        prj = Project(self, uuid)
        _ = prj.get_nodes()
        return prj

    def get(self, endpoint: str, **kwargs) -> Any:
        """Shortcut for GET requests via :meth:`request <API.request>`

        :param endpoint: PolyAnalyst API endpoint
        :param kwargs: :func:`requests.request` keyword arguments
        """
        return self.request(endpoint, method='get', **kwargs)[1]

    def post(self, endpoint: str, **kwargs) -> Any:
        """Shortcut for POST requests via :meth:`request <API.request>`

        :param endpoint: PolyAnalyst API endpoint
        :param kwargs: :func:`requests.request` keyword arguments
        """
        return self.request(endpoint, method='post', **kwargs)[1]

    def request(self, url: str, method: str, **kwargs) -> Response:
        """Sends ``method`` request to ``endpoint`` and returns tuple of
        :class:`requests.Response` and json-encoded content of a response.

        :param url: url or PolyAnalyst API endpoint
        :param method: request method (e.g. GET, POST)
        :param kwargs: :func:`requests.request` keyword arguments
        """
        if not urlparse(url).netloc:
            url = urljoin(self.url, url)
        kwargs['verify'] = self.certfile
        try:
            resp = self._s.request(method, url, **kwargs)
        except requests.RequestException as e:
            raise ClientException(e)
        else:
            return self._handle_response(resp)

    @staticmethod
    def _handle_response(response: requests.Response) -> Response:
        try:
            json = response.json()
        except ValueError:
            json = None

        if response.status_code in (200, 202):
            return response, json

        if isinstance(json, dict) and json.get('error'):
            with contextlib.suppress(KeyError):
                error = json['error']
                error_msg = f"{error['title']}. Message: '{error['message']}'"

        # the old error response format handling
        elif response.status_code == 403:
            if 'are not logged in' in response.text:
                error_msg = 'You are not logged in to PolyAnalyst Server'
            elif 'operation is limited ' in response.text:
                error_msg = ('Access to this operation is limited to project '
                             'owners and administrator')
        elif response.status_code == 500:
            with contextlib.suppress(IndexError, TypeError):
                if json[0] == 'Error':
                    error_msg = json[1]
        else:
            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                error_msg = e

        with contextlib.suppress(NameError):
            raise APIException(error_msg, response.url, response.status_code)

        return response, None


class RemoteFileSystem:
    def __init__(self, api: API):
        self.api = api

    def upload(self, source: Union[str, os.PathLike], dest: str = '', recursive: bool = True) -> None:
        """
        Upload file or folder to PolyAnalyst server.

        Pass ``recursive`` as False to just create folder on the server without
        uploading inner files and folders.

        :param source: path to the file or folder
        :param dest: (optional) path to the folder in the PolyAnalyst's user directory
        :param recursive: (optional) upload subdirectories recursively

        :raise TypeError if ``source`` is not string or path-like object.
               ValueError if ``source`` does not exists
        """
        if not isinstance(source, (str, os.PathLike)):
            raise TypeError('The source parameter should be either string or path-like object.')

        source = pathlib.Path(source)
        if not source.exists():
            raise ValueError(f"Cannot find '{source}': No such file or directory.")

        def _upload(target: pathlib.Path, dest_dir: str) -> None:
            if target.is_file():
                with target.open(mode='rb') as f:
                    self.api.fs.upload_file(f, name=target.name, path=dest_dir)
            elif target.is_dir():
                try:
                    self.api.fs.create_folder(name=target.name, path=dest_dir)
                except APIException as exc:
                    if 'Folder already exists' in exc.message:
                        pass
                    else:
                        raise

                if recursive:
                    for child in target.iterdir():
                        _upload(child, f'{dest_dir}/{target.name}')

        _upload(source, dest)

    def create_folder(self, name: str, path: str = '') -> None:
        """
        Create a new folder inside the PolyAnalyst's user directory.

        :param name: the folder name
        :param path: a relative path of the folder's parent directory
        """
        self.api.post('folder/create', json={'path': path, 'name': name})

    def delete_folder(self, name: str, path: str = '') -> None:
        """
        Delete the folder in the PolyAnalyst's user directory.

        :param name: the folder name
        :param path: a relative path of the folder's parent directory
        """
        self.api.post('folder/delete', json={'path': path, 'name': name})

    def delete_file(self, name: str, path: str = '') -> None:
        """
        Delete the file in the PolyAnalyst's user directory.

        :param name: the filename
        :param path: a relative path of the file's parent directory
        """
        self.api.post('file/delete', json={'path': path, 'name': name})

    def download_file(self, name: str, path: str = '') -> bytes:
        """
        Download the binary content of the file.

        :param name: the filename
        :param path: a relative path of the file's parent directory
        """
        data = self.api.post('file/download', json={'path': path, 'name': name})
        resp, _ = self.api.request(
            urljoin(self.api.url, '/polyanalyst/download'),
            method='get',
            params={'uid': data['uid']}
        )
        return resp.content

    def upload_file(self, file: IO, name: Optional[str] = None, path: str = '') -> None:
        """
        Upload the file to the PolyAnalyst's user directory.

        .. warning::
            Make sure to create a new file or file-like object for every
            :meth:`upload_file <RemoteFileSystem.upload_file>` call!

        .. note::
           Always prefer :meth:`upload <RemoteFileSystem.upload>` over this method.

        :param file: the file or file-like object to upload
        :param name: the filename other than `file`'s name
        :param path: (optional) a relative path of the file's parent directory

        Usage:
            >>> fs = RemoteFileSystem(...)
            >>> with open('CarData.csv', mode='rb') as file:
            >>>     fs.upload_file(file, name='cars.csv', path='/data')
        """
        if file.tell():
            warnings.warn("The file object's current position is not at the beginning of the file."
                          "This will result in uploading only the part of the file!")

        file_name = name or os.path.basename(file.name)
        file_size = _get_file_size(file)
        metadata = {'foldername': path}

        file_endpoint, _ = pytus.create(
            urljoin(self.api.url, 'file/upload'),
            file_name,
            file_size,
            session=self.api._s,
            metadata=metadata
        )

        pytus.resume(
            file,
            file_endpoint,
            session=self.api._s,
            offset=0
        )

        # free up resources on the server if file is not uploaded completely
        try:
            offset = _get_offset(file_endpoint, session=self.api._s)
            if file_size != offset:
                pytus.terminate(file_endpoint, session=self.api._s)
        except requests.exceptions.RequestException:
            pass


class Project:
    """This class maintains all operations with the PolyAnalyst's project and nodes.

    :param api: An instance of :class:`API <API>` class
    :param uuid: The uuid of the project you want to interact with
    """

    def __repr__(self):
        return f'Project({self.uuid})'

    def __init__(self, api: API, uuid: str) -> None:
        self.api = api
        self.uuid = uuid
        self._nodes: Nodes = {}

    def get_nodes(self) -> Nodes:
        """Returns a dictionary of project's nodes information.

        The node value is a dict with a mandatory keys: id, type, status.
        It also may contain errMsg key if last node execution was failed.
        """
        json = self.api.get(
            'project/nodes',
            params={'prjUUID': self.uuid},
            headers={'sid': self.api.sid},
        )
        self._nodes = {node.pop('name'): node for node in json['nodes']}
        return self._nodes

    def get_execution_statistics(self) -> Tuple[Nodes, Dict[str, int]]:
        """Returns the execution statistics for nodes in the project.

        Similar to :meth:`get_nodes() <Project.get_nodes>` but nodes contains
        extra information and the project statistics.
        """
        json = self.api.get(
            'project/execution-statistics',
            params={'prjUUID': self.uuid}
        )
        nodes = {node.pop('name'): node for node in json['nodes']}
        return nodes, json['nodesStatistics']

    def get_tasks(self) -> List[Dict[str, any]]:
        """Returns task list info."""
        json = self.api.get('project/tasks', params={'prjUUID': self.uuid})
        # convert timestamp in milliseconds to python datetime
        for task in json:
            task['startTime'] = datetime.datetime.utcfromtimestamp(task['startTime'] / 1000)
        return json

    def save(self) -> None:
        """Initiates saving of all changes that have been made in the project."""
        self.api.post('project/save', json={'prjUUID': self.uuid})

    def abort(self) -> None:
        """Aborts the execution of all nodes in the project."""
        self.api.post('project/global-abort', json={'prjUUID': self.uuid})

    def execute(self, *nodes: str, wait: bool = False) -> None:
        """Initiate execution of nodes and their children.

        Make sure to sort nodes by the execution flow order when passing
        multiple nodes and wait is True.

        :param nodes: The node names
        :param wait: Wait for nodes to complete execution

        Usage::

          >>> prj.execute('Python')
          >>> prj.execute('Internet Source', 'Export to File')

        Execute all nodes in project(assuming there's no connection between them)::

          >>> prj.execute(*prj.get_nodes())

        :raises APIException if any of nodes is not configured properly
        """
        nodes = list({}.fromkeys(nodes))

        self.get_nodes()
        for node in nodes:
            if self._nodes[node]['status'] == 'incomplete':
                raise APIException(f'Cannot execute "{node}". The node is not configured properly.')

        self.api.post(
            'project/execute',
            json={
                'prjUUID': self.uuid,
                'nodes': [{'type': self._nodes[name]['type'], 'name': name} for name in nodes],
            },
        )
        if wait:
            for node in nodes:
                self.wait_for_completion(node)

    def preview(self, node: str) -> DataSet:
        """Returns first 1000 rows of data from ``node``, texts and strings are
        cutoff after 250 symbols.

        :param node: The node name
        :raises: :class:`APIException <APIException>` when node type is not Dataset or DataSource
        """
        node_type = self._nodes[node]['type']
        if node_type not in ('Dataset', 'DataSource'):
            raise APIException(f"Invalid node type: {node_type} (only 'Dataset' or 'DataSource' are available)")
        return self.api.get(
            'dataset/preview',
            params={
                'prjUUID': self.uuid,
                'name': node,
                'type': self._nodes[node]['type'],
            },
        )

    def unload(self) -> None:
        """Unload the project from the memory and free system resources."""
        self.api.post('project/unload', json={'prjUUID': self.uuid})

    def repair(self) -> None:
        """Initiate the project repairing operation."""
        self.api.post('project/repair', json={'prjUUID': self.uuid})

    def delete(self, force_unload: bool = False) -> None:
        """Delete the project from server.

        :param force_unload: Delete project regardless other users

        By default the project will be deleted only if it's not loaded to memory.
        To delete the project that loaded to memory (there are users working on
        this project right now) set ``force_unload`` to ``True``.
        This operation available only for project owner and administrators, and
        cannot be undone.
        """
        self.api.post(
            'project/delete',
            json={'prjUUID': self.uuid, 'forceUnload': force_unload}
        )

    def set_parameters(self, node: str, node_type: str, parameters: Dict[str, Any]) -> None:
        """Set default parameters of the selected Parameters node in the project.

        :param node: a Parameters node name
        :param node_type: a node type, which parameters need to be set. The types are listed in NodeTypes.
        :param parameters: default parameters of the node to be set.

        :raises ClientException when the node type is not Parameters
        """
        parameters_node = self._nodes[node]
        if parameters_node['type'] != 'Parameters':
            raise ClientException('The node type should be Parameters')

        json: Optional[List[str]]
        json = self.api.post(
            'parameters/configure',
            params={'prjUUID': self.uuid, 'obj': parameters_node['id']},
            json={'type': node_type, 'settings': parameters}
        )
        if json:
            for msg in json:
                warnings.warn(msg)

    def wait_for_completion(self, node: str) -> bool:
        """Waits for the node to complete the execution. Returns True if node have completed successfully and
        False otherwise.

        :param node: The node name
        """
        while True:
            stats = self.get_nodes()[node]
            if stats.get('errMsg'):
                return False
            if stats['status'] == 'synchronized':
                return True
            elif stats['status'] == 'incomplete':
                return False
            time.sleep(1.)
