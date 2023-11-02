"""
polyanalyst6api.api
~~~~~~~~~~~~~~~~~~~

This module contains functionality for access to PolyAnalyst API.
"""
import configparser
import contextlib
import os
import pathlib
import time
import warnings
from typing import Any, Dict, List, Tuple, Union, Optional
from urllib.parse import urljoin, urlparse, parse_qs

import requests
import urllib3

from . import __version__
from .drive import Drive
from .project import Parameters, Project
from .report import Report
from .exceptions import APIException, ClientException, _WrapperNotFound, PABusy

__all__ = ['API']

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.simplefilter('always', UserWarning)  # without this set_parameters will show warnings only once


class API:
    """PolyAnalyst API

    :param url: The scheme, host and port(if exists) of a PolyAnalyst server \
        (e.g. ``https://localhost:5043/``, ``http://example.polyanalyst.com``)
    :param username: The username to log in with
    :param password: (optional) The password for specified username
    :param ldap_server: (optional) LDAP Server address

    If ldap_server is provided, then login will be performed via LDAP Server.

    Usage::

      >>> with API(POLYANALYST_URL, USERNAME, PASSWORD) as api:
      ...     print(api.get_server_info())
    """

    user_agent = f'PolyAnalyst6API python client v{__version__}'

    def __enter__(self) -> 'API':
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()
        self._s.__exit__()

    def __init__(
        self,
        url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        ldap_server: Optional[str] = None,
        **kwargs,
    ):
        if url is None or username is None:
            warnings.warn(
                'Either the Polyanalyst URL or credentials are not provided.'
                'Getting missing data from the credentials file, use of which is deprecated and planned for removal',
                DeprecationWarning,
                2,
            )
            try:
                cfg_path = pathlib.Path.home() / '.polyanalyst6api' / 'config'
                parser = configparser.ConfigParser(allow_no_value=True)
                with open(cfg_path, encoding='utf8') as f:
                    parser.read_file(f)
                default = dict(parser['DEFAULT'])

                url = default['url']
                username = default['username']
                password = default['password']
                ldap_server = default.get(ldap_server)
            except FileNotFoundError:
                raise ClientException(f"The credentials file doesn't exist. Nor credentials passed as arguments")
            except KeyError as exc:
                raise ClientException(f"The credentials file doesn't contain required key: {exc}")

        if not url:
            raise ClientException('The PolyAnalyst URL is empty')

        self.base_url = urljoin(url, '/polyanalyst/api/')
        self.url = urljoin(self.base_url, 'v1.0/')
        self.username = username
        self.password = password or ''
        self.ldap_server = ldap_server

        self._s = requests.Session()
        self._s.verify = kwargs.get('verify', True)
        self._s.headers.update({'User-Agent': self.user_agent})
        self.sid = None  # session identity
        self.drive = Drive(self)

    def get_versions(self) -> List[str]:
        """Returns api versions supported by PolyAnalyst server."""
        return self.request(urljoin(self.base_url, 'versions'), method='get')[1]

    def get_server_info(self) -> Optional[Dict[str, Union[int, str, Dict[str, str]]]]:
        """Returns general server information including build number, version and commit hashes."""
        return self.request(urljoin(self.url, 'server/info'), method='get')[1]

    def login(self) -> None:
        """Logs in to PolyAnalyst Server with user credentials."""
        credentials = {'uname': self.username, 'pwd': self.password}
        if self.ldap_server:
            credentials['useLDAP'] = '1'
            credentials['svr'] = self.ldap_server

        resp, _ = self.request('login', method='post', params=credentials)

        try:
            self.sid = resp.cookies['sid']
        except KeyError:
            self._s.headers['Authorization'] = f"Bearer {resp.headers['x-session-id']}"

    def logout(self) -> None:
        """Logs out current user from PolyAnalyst server."""
        self.get('logout')

    def run_task(self, id: int) -> None:
        """Initiates scheduler task execution.

        :param id: the task ID
        """
        self.post('scheduler/run-task', json={'taskId': id})

    def get_project_import_status(self, import_id: str) -> Dict:
        """Get the status of project import

        :param import_id: the import identifier

        .. versionadded:: 0.24.0
        """
        return self.get('project/import/status', params={'importId': import_id})

    def get_projects_list(self) -> List[Optional[Dict[str, Union[str, int, bool]]]]:
        """Get a list of projects.

        :raises: APIException if version of Polyanalyst older than 2815

        .. versionadded:: 0.31
        """
        return self.get('projects')

    def import_project(
        self,
        file_path: Union[str, os.PathLike],
        project_space: str = '',
        on_conflict: str = 'Cancel',
        wait: bool = False,
    ) -> Union[str, Dict]:
        """
        Import project from file on server file system.

        :param file_path: absolute path to the file on server file system
        :param project_space: the name of the folder in the project manager
            where you want to import the project. The default folder is `Root`.
        :param on_conflict: the strategy to resolve import conflict. Allowed
            options are: Cancel, Overwrite, ChangeExistingId, ChangeImportingId.
            By default, the import will be cancelled if the project already exist.
        :param wait: wait for project import to finish. False by default.

        :return: import identifier if `wait` is False and import status otherwise

        .. versionadded:: 0.24.0
        """
        resp, _ = self.request(
            'project/import',
            method='post',
            json={
                'fileName': os.fspath(file_path),
                'folderPath': project_space,
                'conflictResolveMethod': on_conflict,
            },
        )
        location = resp.headers.get('location')
        qs = parse_qs(urlparse(location).query)
        import_id = qs['importId'][0]

        if not wait:
            return import_id

        while True:
            time.sleep(1)
            status = self.get_project_import_status(import_id)
            # status has only empty state key when the server rebooted during the project import: T32492#776729
            if status.get('progress', 100) == 100:
                return status

    def project(self, uuid: str, wait: bool = True) -> Project:
        """Returns :class:`Project <Project>` instance with given uuid.

        :param uuid: The project uuid

        .. versionchanged:: 0.31
            Added loading of the project when calling the method: use the `wait`
            parameter to wait for the project to load. Defaults to ``False``.
        """
        prj = Project(self, uuid, wait)
        prj._update_node_list()
        return prj

    def report(self, uuid: str) -> Report:
        """Returns :class:`Report <Report>` instance with given report uuid.

        :param uuid: The report uuid

        .. versionadded:: 0.30.0
        """
        return Report(self, uuid)

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

    def request(self, url: str, method: str, **kwargs) -> Tuple[requests.Response, Any]:
        """Sends ``method`` request to ``endpoint`` and returns tuple of
        :class:`requests.Response` and json-encoded content of a response.

        :param url: url or PolyAnalyst API endpoint
        :param method: request method (e.g. GET, POST)
        :param kwargs: :func:`requests.request` keyword arguments
        """
        if not urlparse(url).netloc:
            url = urljoin(self.url, url)
        try:
            resp = self._s.request(method, url, **kwargs)
        except requests.RequestException as exc:
            raise ClientException(exc)
        else:
            return self._handle_response(resp)

    @staticmethod
    def _handle_response(response: requests.Response) -> Tuple[requests.Response, Any]:
        try:
            json = response.json()
        except ValueError:
            json = None

        if response.status_code == 503:
            raise PABusy

        if response.status_code in (200, 202):
            return response, json

        if isinstance(json, dict) and json.get('error'):
            with contextlib.suppress(KeyError):
                error = json['error']
                if 'The wrapper with the given GUID is not found on the server' == error['message']:
                    raise _WrapperNotFound
                if error['title']:
                    error_msg = f"{error['title']}. Message: '{error['message']}'"
                else:
                    error_msg = error['message']

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
                error_msg = str(exc)

        with contextlib.suppress(NameError):
            raise APIException(error_msg, response.url, response.status_code)

        return response, None

    @property
    def fs(self):
        warnings.warn('"fs" attribute has been renamed "drive"', DeprecationWarning, 2)
        return self.drive

    def get_parameters(self) -> List[Dict[str, Union[str, List]]]:
        """
        Returns list of nodes with parameters supported by ``Parameters`` node.

        .. deprecated:: 0.18.0
            Use :meth:`Parameters.get` instead.
        """
        warnings.warn(
            'API.get_parameters() is deprecated, use Parameters.get() instead.',
            DeprecationWarning,
            stacklevel=2,
        )

        class ProjectStub:
            api = self

        return Parameters(ProjectStub(), None).get()


# deprecated, use Parameters.get instead
NodeTypes = []
