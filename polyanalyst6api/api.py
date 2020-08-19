"""
polyanalyst6api.api
~~~~~~~~~~~~~~~~~~~

This module contains functionality for access to PolyAnalyst API.
"""

import contextlib
import datetime
import functools
import os
import pathlib
import time
import warnings
from typing import Any, Dict, List, Tuple, Union, Optional, IO, Iterator
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
Node = Dict[str, Union[str, int]]
_DataSet = List[Dict[str, Any]]
JSON_VAL = Union[bool, str, int, float, None]

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

    :param url: The scheme, host and port(if exists) of a PolyAnalyst server \
        (e.g. ``https://localhost:5043/``, ``http://example.polyanalyst.com``)
    :param username: The username to login with
    :param password: (optional) The password for specified username
    :param ldap_server: (optional) LDAP Server address
    :param version: (optional) Choose which PolyAnalyst API version to use. Default: ``1.0``

    If ldap_server is provided, then login will be performed via LDAP Server.

    Usage::

      >>> import polyanalyst6api
      >>> api = polyanalyst6api.API(URL, USERNAME, PASSWORD)
      >>> api.login()

    Or as a context manager::

      >>> with polyanalyst6api.API(URL, USERNAME, PASSWORD) as api:
      ...     assert api.sid
    """

    _api_path = '/polyanalyst/api/'
    _valid_api_versions = ['1.0']
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
            return self.request(urljoin(self.base_url, 'versions'), method='get')[1]
        except APIException:
            return ['1.0']

    def get_server_info(self) -> Optional[Dict[str, Union[int, str, Dict[str, str]]]]:
        """Returns general server information including build number, version and commit hashes."""
        _, data = self.request(urljoin(self.url, 'server/info'), method='get')
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

        resp, _ = self.request('login', method='post', params=credentials)
        self.sid = resp.cookies['sid']

    def logout(self) -> None:
        """NOT IMPLEMENTED YET."""

    def run_task(self, id: int) -> None:
        """Initiates scheduler task execution.

        :param id: the task ID
        """
        self.post('scheduler/run-task', json={'taskId': id})

    def project(self, uuid: str) -> 'Project':
        """Returns :class:`Project <Project>` instance with given uuid.

        :param uuid: The project uuid
        """
        prj = Project(self, uuid)
        prj._update_node_list()  # check that the project with given uuid exists
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
        except requests.RequestException as exc:
            raise ClientException(exc)
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
                error_msg = 'Access to this operation is limited to project owners and administrator'
        elif response.status_code == 500:
            with contextlib.suppress(IndexError, TypeError):
                if json[0] == 'Error':
                    error_msg = json[1]
        else:
            try:
                response.raise_for_status()
            except requests.HTTPError as exc:
                error_msg = exc

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

        :raise TypeError if ``source`` is not string or path-like object.\
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

        Usage::
          >>> fs = RemoteFileSystem(...)
          >>> with open('CarData.csv', mode='rb') as file:
          ...     fs.upload_file(file, name='cars.csv', path='/data')
        """
        if file.tell():
            warnings.warn(
                "The file object's current position is not at the beginning of the file."
                "This will result in uploading only the part of the file!"
            )

        file_name = name or os.path.basename(file.name)
        file_size = _get_file_size(file)

        file_endpoint, _ = pytus.create(
            urljoin(self.api.url, 'file/upload'),
            file_name,
            file_size,
            session=self.api._s,
            metadata={'foldername': path},
        )

        pytus.resume(file, file_endpoint, session=self.api._s, offset=0)

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
        return f'<Project [{self.uuid}]>'

    def __init__(self, api: API, uuid: str) -> None:
        self.api = api
        self.uuid = uuid
        self._node_list: List[Node] = []

    def get_node_list(self) -> List[Node]:
        """Returns a list of project nodes.

        .. versionadded:: 0.15.0
        """
        return self.api.get(
            'project/nodes',
            params={'prjUUID': self.uuid},
            headers={'sid': self.api.sid},
        )['nodes']

    def get_execution_stats(self) -> List[Node]:
        """Returns nodes execution statistics.

        .. versionadded:: 0.15.0
        """
        return self.api.get('project/execution-statistics', params={'prjUUID': self.uuid})['nodes']

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

    def execute(self, *args: Union[str, Dict[str, str]], wait: bool = False) -> None:
        """Initiate execution of nodes and their children.

        :param args: node names and/or dicts with name and type of nodes
        :param wait: wait for nodes execution to complete

        Usage::

          >>> prj.execute('Internet Source', 'Python')

        or, if there are several nodes in the project with the same name, pass
        them as a dict with mandatory ``name`` and ``type`` keys (and because of this,
        you can also pass items of :func:`get_node_list`)

          >>> prj.execute(
          ...     {'name': 'Example node', 'type': 'DataSource'},
          ...     {'name': 'Example node', 'type': 'Dataset'},
          ...     'Federated Search',
          ...     prj.get_node_list()[1],
          ... )

        use ``wait=True`` to wait for the passed nodes execution to complete.
        Note that the other nodes execution started by this command will not be awaited.

          >>> prj.execute('Export to MS Word', wait=True)
        """
        nodes = []
        for arg in args:
            node = self._find_node(arg)
            nodes.append({'name': node['name'], 'type': node['type']})

        self.api.post('project/execute', json={'prjUUID': self.uuid, 'nodes': nodes})
        if wait:
            for node in nodes:
                self.wait_for_completion(node)

    def preview(self, node: Union[str, Dict[str, str]]) -> _DataSet:
        """Returns first 1000 rows of data from ``node``, texts and strings are
        cutoff after 250 symbols.

        :param node: node name or dict with name and type of node

        .. deprecated:: 0.16.0
           Use :method:: prj.dataset().preview() instead.

        Usage::

          >>> data_set = prj.preview('Python')

        or, pass dict if the project contains several nodes with the same name
          >>> data_set = prj.preview({'name': 'Python', 'type': 'Dataset'})
        """
        return self.dataset(node).preview()

    def dataset(self, node: Union[str, Dict[str, str]]):
        """Get dataset object

        :param node: node name or dict with name and type of the node

        .. versionadded:: 0.16.0
        """
        return DataSet(self, self._find_node(node))

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
        self.api.post('project/delete', json={'prjUUID': self.uuid, 'forceUnload': force_unload})

    def set_parameters(
        self,
        node: Union[str, Dict[str, str]],
        node_type: str,
        parameters: Dict[str, Any],
        declare_unsync: bool = True,
        hard_update: bool = True,
    ) -> None:
        """Set default parameters of the selected Parameters node in the project.

        :param node: name or dict with name and type of Parameters node
        :param node_type: node type, which parameters need to be set. The types are listed in NodeTypes.
        :param parameters: default parameters of the node to be set.
        :param declare_unsync: reset the status of the Parameters node.
        :param hard_update: update every child node with new parameters if True, \
            otherwise reset their statuses. Works only if declare_unsync is True.
        """
        warns: Optional[List[str]]
        warns = self.api.post(
            'parameters/configure',
            params={'prjUUID': self.uuid, 'obj': self._find_node(node)['id']},
            json={
                'type': node_type,
                'settings': parameters,
                'declareUnsync': declare_unsync,
                'hardUpdate': hard_update,
            },
        )
        if warns:
            for msg in warns:
                warnings.warn(msg)

    def wait_for_completion(self, node: Union[str, Dict[str, str]]) -> bool:
        """Waits for the node to complete the execution. Returns True if node have
        completed successfully and False otherwise.

        :param node: node name or dict with name and type of node
        """
        time.sleep(0.5)  # give pa time to update node statuses
        while True:
            self._update_node_list()
            stats = self._find_node(node)

            if stats.get('errMsg'):
                return False
            if stats['status'] == 'synchronized':
                return True
            if stats['status'] == 'incomplete':
                return False

            time.sleep(1)

    def _update_node_list(self) -> None:
        self._node_list = self.get_node_list()

    def _find_node(self, node_: Union[str, Dict[str, str]]) -> Optional[Node]:
        for node in self._node_list:
            if isinstance(node_, str):
                if node['name'] == node_:
                    return node
            else:
                if node['name'] == node_['name'] and node['type'] == node_['type']:
                    return node

    def get_nodes(self) -> Nodes:
        """Returns a dictionary of project's nodes information.

        The node value is a dict with a mandatory keys: id, type, status.
        It also may contain errMsg key if last node execution was failed.

        .. deprecated:: 0.15.0
           Use :func:`get_node_list` instead.
        """
        warnings.warn(
            'Project.get_nodes() is deprecated, use Project.get_node_list() instead.', DeprecationWarning, stacklevel=2
        )
        json = self.api.get(
            'project/nodes',
            params={'prjUUID': self.uuid},
            headers={'sid': self.api.sid},
        )
        return {node.pop('name'): node for node in json['nodes']}

    def get_execution_statistics(self) -> Tuple[Nodes, Dict[str, int]]:
        """Returns the execution statistics for nodes in the project.

        Similar to :meth:`get_nodes() <Project.get_nodes>` but nodes contains
        extra information and the project statistics.

        .. deprecated:: 0.15.0
           Use :func:`get_execution_stats` instead.
        """
        warnings.warn(
            'Project.get_execution_statistics() is deprecated, use Project.get_execution_stats() instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        json = self.api.get('project/execution-statistics', params={'prjUUID': self.uuid})
        nodes = {node.pop('name'): node for node in json['nodes']}
        return nodes, json['nodesStatistics']


def retry_on_invalid_guid(func):
    @functools.wraps(func)
    def wrapper(cls, *args, **kwargs):
        try:
            return func(cls, *args, **kwargs)
        except APIException:
            cls._update_guid()
            return func(cls, *args, **kwargs)

    return wrapper


class DataSet:
    def __init__(self, prj: Project, node: Node):
        self._prj = prj
        self._api = prj.api
        self._node = node
        self.guid: Optional[str] = None

    @retry_on_invalid_guid
    def get_info(self) -> Dict[str, Any]:
        return self._api.get('dataset/info', params={'wrapperGuid': self.guid})

    @retry_on_invalid_guid
    def get_progress(self) -> Dict[str, Union[int, str]]:
        return self._api.get('dataset/progress', params={'wrapperGuid': self.guid})

    def preview(self):
        """Returns first 1000 rows of data from ``node``, texts and strings are
        cutoff after 250 symbols.
        """
        return self._api.get(
            'dataset/preview',
            params={'prjUUID': self._prj.uuid, 'name': self._node['name'], 'type': self._node['type']},
        )

    def iter_rows(self, start: int = 0, stop: Optional[int] = None) -> Iterator[Dict[str, JSON_VAL]]:
        """
        Iterate over dataset rows.

        :param start:
        :param stop:

        :raises ValueError if start or stop is out of datasets' row range

        Usage::

          download first 10 rows
          >>> head = []
          >>> for row in ds.iter_rows(0, 10):
          ...     head.append(row)
          download full dataset
          >>> table = list(ds.iter_rows())
          convert downloaded dataset to pandas.DataFrame
          >>> df = pandas.DataFrame(table)
        """
        info = self.get_info()
        max_row = info['rowCount']
        if stop is None:
            stop = max_row

        # предпологается что если stop определен то пользователь в курсе количества строк в датасете
        if not 0 <= start <= stop <= max_row:
            raise ValueError(f'start and stop arguments must be within dataset row range: (0, {max_row})')

        rows = self._values(stop)['table']
        get_text = self._cell_text

        class RowIterator:
            def __init__(self):
                self.idx = start

            def __iter__(self):
                return self

            def __next__(self):
                if self.idx >= stop:
                    raise StopIteration

                result = {}
                for column in info['columnsInfo']:
                    if column['flags'].get('getTextAlways'):
                        result[column['title']] = get_text(self.idx, column['id'], column['title'])
                    # elif column['type'] == 'DateTime':  # todo convert to python datetime?
                    else:
                        result[column['title']] = rows[self.idx][column['id']]

                self.idx += 1
                return result

        return RowIterator()

    def _update_guid(self) -> None:
        self.guid = self._api.get(
            'dataset/wrapper-guid',
            params={'prjUUID': self._prj.uuid, 'obj': self._node['id']},
        )['wrapperGuid']

    @retry_on_invalid_guid
    def _values(self, row_count: int) -> Dict[str, Union[List, Dict]]:
        return self._api.get('dataset/values', json={'wrapperGuid': self.guid, 'rowCount': row_count})

    @retry_on_invalid_guid
    def _cell_text(self, row: int, col: int, _title) -> str:
        return self._api.get(
            'dataset/cell-text',
            json={
                'wrapperGuid': self.guid,
                'row': row,
                'col': col,
                # todo remove next keys
                'colTitle': _title,
                'offset': 0,
                'count': 0,
            },
        )['text']
