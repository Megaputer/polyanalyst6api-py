"""
polyanalyst6api.project
~~~~~~~~~~~~~~~~~~~~~~~

This module contains functionality for access to PolyAnalyst Analytical Client API.
"""
import datetime
import functools
import math
import os
import time
import warnings
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict, List, Union, Optional, Tuple, Iterator

from .exceptions import APIException, ClientException, _WrapperNotFound, PABusy

__all__ = ['Project', 'Parameters', 'DataSet']

# type hints
Node = Dict[str, Union[str, int]]
Nodes = Dict[str, Dict[str, Union[int, str]]]
_DataSet = List[Dict[str, Any]]
JSON_VAL = Union[bool, str, int, float, None]


class Project:
    """This class maintains all operations with the PolyAnalyst's project and nodes.

    :param api: An instance of :class:`API <API>` class
    :param uuid: The uuid of the project you want to interact with

    .. versionchanged:: 0.31.0
           Added nodes list updating while initializing the class
    """

    def __repr__(self):
        return f'<Project [{self.uuid}]>'

    def __init__(self, api, uuid: str):
        self.api = api
        self.uuid = uuid
        self._node_list: List[Node] = self.get_node_list() # automatically loads a project

    def get_node_list(self) -> List[Node]:
        """Returns a list of project nodes.

        .. versionadded:: 0.15.0
        """
        return self.api.get('project/nodes', params={'prjUUID': self.uuid})['nodes']

    def get_report_list(self) -> List[Dict[str, str]]:
        """Returns a list of project reports. 

        .. versionadded:: 0.30.0
        """
        return self.api.get('project/reports', params={'prjUUID': self.uuid})

    def get_execution_stats(self, skip_hidden: Optional[bool] = None) -> List[Node]:
        """Returns nodes execution statistics.

        :param skip_hidden: Return statistics only of nodes in the project (i.e.
            exclude publication and compound nodes).

        .. versionadded:: 0.15.0
        .. versionchanged:: 0.25.0
           Added `skip_hidden` optional parameter.
        """
        params = {'prjUUID': self.uuid}
        if skip_hidden is not None:
            # to allow using older PA's that don't have this arg and return 'redundant parameter in query' error
            params['skipHiddenNodes'] = 'true' if skip_hidden else 'false'
        return self.api.get('project/execution-statistics', params=params)['nodes']

    def get_tasks(self) -> List[Dict[str, Any]]:
        """Returns task list info."""
        json = self.api.get('project/tasks', params={'prjUUID': self.uuid})
        # convert timestamp in milliseconds to python datetime
        for task in json:
            task['startTime'] = datetime.datetime.utcfromtimestamp(task['startTime'] / 1000)
        return json

    def save(self) -> None:
        """Initiates saving of all changes that have been made in the project."""
        self.api.post('project/save', json={'prjUUID': self.uuid})

    def get_save_status(self, save_id: int) -> Dict[str, Any]:
        """Get the status of project save
        
        :param save_id: the save identifier
        
        :return: project save status
        """
        return self.api.get('project/save/status', params={'asyncOperationId': save_id})

    def folder_list(self) -> List[Dict]:
        """Gets the list of folders
        
        :return: list of folders
        """
        return self.api.get('project/folders')
    
    def create_folder(self, name: str, folder_path: str = "", description: str = "") -> None:
        """This operation creates a folder in the Project manager
        
        param name: folderName is a name of the folder to create
        param folder_path: path to a parent folder
        param description: the description field is used to set a folder description
        """ 
        self.api.post('project/folder/create', json={'folderName': name, 'parentPath': folder_path, "description": description})

    def delete_folder(self, folder_path: str, recursive: bool = False) -> None:
        """This operation deletes a folder from the Project manager
        
        param folder_path: path to a user is folder
        param recursive: flag to delete subfolders and projects inside the folder.
        """
        self.api.post('project/folder/delete', json={'folderPath': folder_path, 'recursive': recursive})

    def rename_folder(self, folder_path: str, new_name: str, description: str = "") -> None:
        """This operation renames a folder in the Project manager and sets a description for the folder
        
        param folder_path: path to a user is folder
        param new_name: sets a new name
        param description: sets a new description
        """
        self.api.post('project/folder/rename', json={'folderPath': folder_path, 'name': new_name, 'description': description})

    def project_import(self, abs_path_file: str, folder_path: str, conflict_method: str) -> None:
        """This operation allows users to import a project onto the server

        param abs_path_file: The fileName parameter is used to specify a path to a project file
        param folder_path: The folderPath parameter denotes a folder where a project is being imported into
        """
        self.api.post('project/import', json={'fileName': abs_path_file, 'folderPath': folder_path, 'conflictResolveMethod': conflict_method})

    def project_import_status(self, import_id: str) -> List[Dict[str, Any]]:
        """Checking the status of the import operation
        
        :return: project import status

        param import_id: ID of the export operation
        """
        return self.api.get('project/import/status', params={'importId': import_id})
    
    def project_export(self, file_name: str, file_format: str, ids: list, compression_level: int = 5, multi: bool = False, 
                       keep_slice_statistics: bool = False, keep_backups: bool = False, keep_macros_and_vars: bool = False, 
                       overwrite_existing: bool = False) -> None:
        """This operation allows users to export a project from the server

        param file_name: name of the project
        param file_format: format to export
        param ids: IDs of the project
        param compression_level: level of compression
        param multi: flag to show there are several projects to export
        param keep_slice_statistics: flag to keep slice usage statistics
        param keep_backups: flag to keep backup versions
        param keep_macros_and_vars: flag to keep user and server macros and variables
        param overwrite_existing: flag to overwrite the existing file

        :raises ValueError if there are no arguments "file_name", "file_format", "ids"
        :raises ValueError if ids is not a list or invalid "file_format"
        """
        if not file_name or not file_format or not ids:
            raise ValueError("file_name, file_format and ids parameters are required")
    
        if not isinstance(ids, list):
            raise ValueError("ids must be an array of strings")
    
        valid_formats = ['pa6', 'ps6', 'paar6', 'psar6', 'pagridar6']
        if file_format not in valid_formats:
            raise ValueError("Invalid file_format. Must be one of: pa6, ps6, paar6, psar6, pagridar6")
    
        request_body = {
            "fileName": file_name,
            "fileFormat": file_format,
            "ids": ids,
            "compressionLevel": compression_level,
            "multi": multi,
            "keepSliceStatistics": keep_slice_statistics,
            "keepBackups": keep_backups,
            "keepMacrosAndVars": keep_macros_and_vars,
            "overwriteExisting": overwrite_existing
        }
    
        self.api.post('project/export', json=request_body)

    def project_export_status(self):
        """Checking the status of the export operation
        
        :return: A status of the export operation will be returned
        """
        return self.api.get('project/export/status', params={'exportId': self.uuid})
        
    def project_config_set(self, actions: list) -> None:
        """This operation updates the project configuration 
        Note that appropriate project rights are needed to perform the operation
        
        param actions: parameters to be changed
        """
        request_body = {
            "prjUUID": self.uuid,
            "actions": actions
        }

        self.api.post('project/config/update', json=request_body)

    def duplicate(self, name: str, folder_path: str = "", spaceId: str = None):
        """This operation allows users to duplicate a project. 
        The operation is available only for project owners and administrators and can not be undone.
        
        :param name: sets the name for the project copy
        :param folder_path: parameter is a folder in which a project duplicate must be created
        """
        if not folder_path:
            folder_path = ""

        request_body = {
            "prjUUID": self.uuid,
            "name": name,
            "folderPath": folder_path,
            "spaceId": spaceId
        }

        request_body = {k: v for k, v in request_body.items() if v is not None}
        self.api.post('project/duplicate', json=request_body)

    def get_duplicating_status(self, duplicate_id: int) -> Dict[str, Any]:
        """Get the status of project duplicate
        
        :param duplicate_id: the duplicate identifier

        :return: project duplicate status
        """
        return self.api.get('project/duplicate/status', params={'asyncOperationId': duplicate_id})

    def move(self, folder_path: str) -> None:
        """This operation moves a project to a specified folder"""
        if folder_path == "":
            folder_path = "/" 
        payload = {
            'ids': [self.uuid],
            'folderPath': folder_path
        } 
        self.api.post('project/move', json=payload)

    def dependencies(self) -> Dict:
        """This operation returns a list of project dependencies.
        
        :return: list of project dependencies
        """
        payload = {
            'ids': [self.uuid]
        }
        return self.api.get('project/dependencies', json=payload)
    
    def get_project_config(self, prefix: str = "") -> List[Dict]:
        """This operation returns a list of the project settings
        
        :return: list of the project configuration

        :param prefix: The parameter allows to get only a part of the project configuration
        """
        return self.api.get('project/config', params={'prjUUID': self.uuid, 'prefix': prefix})
     
    def spaces(self) -> List[Dict]:
        """This operation returns a list of project spaces.
        
        :return: project spaces
        """
        return self.api.get('project/spaces')
    
    def rename(self, new_name: Optional[str] = None, new_description: Optional[str] = None) -> None:
        """
        :param new_name: sets a new project name
        :param new_description: sets a new project description

        :raises: ValueError if no parameter is set

        This operation allows users to rename a project and to give it a new description. 
        The operation is available only for project owners and administrators and can not be undone.
        """
        if not new_name and not new_description:
            raise ValueError("Must be specify one of the 'name' or 'description' parameters'")
    
        payload = {'prjUUID': self.uuid}
    
        if new_name:
            payload['name'] = new_name
        if new_description:
            payload['description'] = new_description
    
        self.api.post('project/rename', json=payload)

    def get_project_list(self) -> List[Dict[str, Any]]:
        """This operation returns a list of projects of the server
        
        :return: list of projects
        """
        return self.api.get('projects')

    def abort(self) -> None:
        """Aborts the execution of all nodes in the project."""
        self.api.post('project/global-abort', json={'prjUUID': self.uuid})

    def execute(
            self, *args: Union[str, Dict[str, str]], wait: bool = False, ignore_first_n_pabusy: int = 0
    ) -> Optional[int]:
        """
        Initiates execution of nodes and returns execution wave identifier.

        :param args: node names and/or dicts with name and type of nodes
        :param wait: wait for nodes execution to complete
        :param ignore_first_n_pabusy: (deprecated) when waiting for execution to complete skip the first specified
            numbers of PABusy

        .. versionchanged:: 0.34.0
           Added `ignore_first_n_pabusy` parameter

        Usage::

          >>> wave_id = prj.execute('Internet Source', 'Python')

        use ``wait=True`` to wait for the passed nodes execution to complete.

          >>> prj.execute('Export to MS Word', wait=True)

        or, if there are several nodes in the project with the same name, pass
        them as dicts with `name` and `type` keys (and because of this, you can
        also pass items of :meth:`Project.get_node_list`)

          >>> prj.execute(
          ...     {'name': 'Example node', 'type': 'DataSource'},
          ...     {'name': 'Example node', 'type': 'Dataset'},
          ...     'Federated Search',
          ...     prj.get_node_list()[1],
          ... )

        or, if you want to execute all nodes, call this method with no ``args``:

          >>> prj.execute()
        """

        if ignore_first_n_pabusy:
            warnings.warn(
                'ignore_first_n_pabusy is deprecated, use pabusy_timeout parameter in API class instead.',
                DeprecationWarning,
                stacklevel=2,
            )

        nodes = []
        for arg in args:
            node = self._find_node(arg)
            nodes.append({'name': node['name'], 'type': node['type']})

        resp, _ = self.api.request('project/execute', 'POST', json={'prjUUID': self.uuid, 'nodes': nodes})

        location = resp.headers.get('location')
        query = urlparse(location).query
        try:
            wave_id = int(parse_qs(query).get('executionWave')[0])
        except TypeError:
            wave_id = None

        if wait:
            if wave_id is None:
                for node in nodes:
                    self.wait_for_completion(node)  # type: ignore
                return

            while True:
                time.sleep(1)
                try:
                    if not self.is_running(wave_id):
                        break
                except PABusy:
                    ignore_first_n_pabusy -= 1
                    if ignore_first_n_pabusy <= 0:
                        raise

        return wave_id

    def execute_to(self, node: Union[str, Dict[str, str]], wait: bool = False) -> Optional[int]:
        """
        Execute a sequence of nodes to the given node.

        Similar to :meth:`Project.execute`, except for two differences:
          - accepts only one node
          - execution of a sequence of nodes stops at the given node and does not continue further

        :param node: node name or a dict with node name and type
        :param wait: wait until node is executed

        :return: execution task identifier if `wait` is False else None

        .. versionadded:: 0.30.0
        """
        resp, _ = self.api.request(
            'project/execute-to-node',
            method='post',
            json={'prjUUID': self.uuid, 'nodes': [self._find_node(node)]},
        )
        location = resp.headers.get('location')
        query = urlparse(location).query
        wave_id = int(parse_qs(query).get('executionWave')[0])

        if not wait:
            return wave_id

        while self.is_running(wave_id):
            time.sleep(1)

    def is_running(self, wave_id: int) -> bool:
        """
        Checks that execution wave is still running in the project.

        If `wave_id` is `-1` then the project is checked against any active
        execution, saving, publishing operations.

        :param wave_id: Execution wave identifier
        """
        data = self.api.get(
            'project/is-running',
            params={'prjUUID': self.uuid, 'executionWave': wave_id},
        )
        return bool(data['result'])

    def dataset(self, node: Union[str, Dict[str, str]]):
        """Get dataset wrapper object.

        :param node: node name or dict with name and type of the node

        .. versionadded:: 0.16.0
        """
        return DataSet(self, self._find_node(node))

    def parameters(self, name: str):
        """Get parameters wrapper object.

        :param name: Parameters node name

        .. versionadded:: 0.18.0
        """
        return Parameters(self, self._find_node(name)['id'])

    def _get_load_status(self, load_id: int) -> Dict[str, Any]:
        """Get the status of project load.

        :param load_id: the load identifier
        :raises: APIException if bad load_id or version of PolyAnalyst older than 2815

        :return: project loading status

        .. versionadded:: 0.31
        """

        return self.api.get('project/load/status', params={'asyncOperationId': load_id})

    def load(self, wait: bool = False) -> Union[str, Dict[str, Any]]:
        """Load project to the memory.

        :param wait: wait until the project loading is completed. Defaults to ``False``.
        :raises: APIException if version of PolyAnalyst older than 2815

        :return: load identifier if `wait` is False and load status otherwise

        .. versionadded:: 0.31
        """
        resp, _ = self.api.request('project/load', method='post', json={'prjUUID': self.uuid})
        location = resp.headers.get('location')
        qs = parse_qs(urlparse(location).query)
        load_id = qs['asyncOperationId'][0]

        if not wait:
            return load_id

        while True:
            time.sleep(1)
            status = self._get_load_status(load_id)
            if status.get('status') not in ('Processing'):
                if status.get('status') in ('Error'):
                    raise ClientException(f"Failed to load project: {status.get('message')}")
                return status

    def status(self):
        """Get project status.

        :raises: APIException if version of PolyAnalyst older than 2815

        :return: project status

        .. versionadded:: 0.31
        """
        return self.api.get('project/status', params={'prjUUID': self.uuid})
    
    def info(self):
        """This operation returns information about a project.
        
        :return: project information
        """
        return self.api.get('project/info', params={'prjUUID': self.uuid})
        
    def unload(self, force_unload: bool = False) -> None:
        """
        Unload the project from the memory.

        From version `0.26.2` this function ensures that the project is unloaded despite PABusy error
        by repeating requests (maximum 10) until PA either returns an ok response or
        returns an error 'the project has not been opened', which means project is also unloaded.

        :raises: PABusy if PABusy returned for all 10 request attempts
        :raises: APIException if the project has been unloaded before this function was called

        .. versionchanged:: 0.30.0
           Added `force_unload` parameter, which when used allows server to unload a project even with running nodes
        """
        data = {'prjUUID': self.uuid}
        if force_unload:
            data['forceUnload'] = True

        for n in range(10):
            try:
                self.api.post('project/unload', json=data)
                break
            except PABusy:
                time.sleep(0.1 * (2 ** (n - 1)))  # urllib's backoff formula
            except APIException as e:
                if 'has not been opened by user administrator' in str(e) and n != 0:
                    warnings.warn(str(e))
                    break
                else:
                    raise
        else:
            raise PABusy

    def repair(self) -> None:
        """Initiate the project repairing operation."""
        self.api.post('project/repair', json={'prjUUID': self.uuid})

    def delete(self, force_unload: bool = False) -> None:
        """Delete the project from server.

        :param force_unload: Delete project regardless other users

        By default, the project will be deleted only if it's not loaded to memory.
        To delete the project that loaded to memory (there are users working on
        this project right now) set ``force_unload`` to ``True``.
        This operation available only for project owner and administrators, and
        cannot be undone.
        """
        self.api.post('project/delete', json={'prjUUID': self.uuid, 'forceUnload': force_unload})

    def _update_node_list(self) -> None:
        self._node_list = self.get_node_list()

    def _find_node(self, node_: Union[str, Dict[str, str]]) -> Node:
        if isinstance(node_, str):
            name_, type_ = node_, None
        else:
            name_, type_ = node_['name'], node_['type']

        for node in self._node_list:
            if node['name'] == name_ and (type_ is None or node['type'] == type_):
                return node

        raise APIException(f"Node not found: name='{name_}', type='{type_}'", status_code=500)

    def wait_for_completion(self, node: Union[str, Dict[str, str]], wave_id: Optional[int] = None) -> bool:
        """
        Waits for the node in a sequence of nodes to complete. Returns `True` if
        node have completed successfully and `False` otherwise.

        Unlike `execute(..., wait=True)`, which returns only after an entire node
        sequence has completed, this method returns immediately after the specified
        node has completed.

        :param node: Node name or dict with name and type of node that runs within execution wave
        :param wave_id: Execution wave identifier

        .. deprecated:: 0.17.0
           Use :meth:`Project.is_running` instead.

        .. versionchanged:: 0.23.0
           Introduced this deprecated method back. Added `wave_id` argument.
        """
        if not wave_id:
            warnings.warn(
                'It is recommended to use `Project.wait_for_completion` with `wave_id` argument',
                UserWarning,
                stacklevel=2,
            )

        time.sleep(0.5)  # give pa time to update node statuses
        while True:
            self._update_node_list()
            stats = self._find_node(node)

            if stats.get('errMsg'):
                return False
            elif stats['status'] == 'synchronized':
                return True
            elif stats['status'] == 'incomplete':
                return False
            elif wave_id and not self.is_running(wave_id):
                return False

            time.sleep(1)

    def export(
        self, file_path: Union[str, os.PathLike], options: Optional[Dict] = None, wait: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """
        Export project to a server file system.

        :param file_path: The path to which you want to export a project. Can be absolute path or contain PolyAnalyst
            alias, i.e. `Open access folder` or `User home folder`. The file extension defines project format: ``ps6``,
            ``pa6``, ``psar6``, ``paar6`` or ``pagridar6``.
        :param options: Dict of export parameters:
            *

              | ``ids``: List of project IDs to export into one file: ``psar6``, ``paar6`` or ``pagridar6``. Defaults\
                to current project.
              | ``compressionLevel``: Compression level: ``store``, ``fastest``, ``fast``, ``normal``, ``maximum`` or\
                ``ultra``. Defaults to ``normal``.
              | ``keepBackups``: Keep backup versions. Defaults to ``True``.
              | ``keepMacrosAndVars``: Keep user and server macros and variables. Defaults to ``True``.
              | ``keepSliceStatistics``: Keep slice usage statistics. Defaults to ``False``.
              | ``overwriteExisting``: Replace existing file. Defaults to ``False``.
              | ``dicts``: Dict of project dictionaries. Defaults to ``{}``.
              | ``usedDicts``: Dict of server-side non-embedded dictionaries. Defaults to ``{}``.
              | ``usedParsers``: List of used parsers to include. Defaults to ``[]``.
        :param wait: Wait until the project export is completed. Defaults to ``False``.
        :raises ClientException: if ``compressionLevel`` is not one of the defined

        :return: export identifier if `wait` is False and export status otherwise

        Usage::

          >>> prj.export('@administrator@/example.pa6')
          >>> # or
          >>> status = prj.export(
          >>>     'C:/Users/Public/Documents/test.paar6',
          >>>     {
          >>>         'overwriteExisting': True,
          >>>         'compressionLevel': 'maximum',
          >>>     },
          >>>     wait=True
          >>> )

        .. versionadded:: 0.28.0
        """
        if options is None:
            options = {}

        options['fileName'] = os.fspath(file_path)
        options['fileFormat'] = os.fspath(file_path).split('.')[-1]
        options['ids'] = options.get('ids', [self.uuid])

        cmpr = options.get('compressionLevel')
        compression_levels = {'store': 0, 'fastest': 1, 'fast': 3, 'normal': 5, 'maximum': 7, 'ultra': 9}
        if cmpr:
            try:
                options['compressionLevel'] = compression_levels[cmpr.lower()]
            except KeyError as e:
                raise ClientException(f'Unknown compression level: {cmpr}') from e

        defaults = {
            'compressionLevel': 5,
            'keepBackups': True,
            'keepMacrosAndVars': True,
            'keepSliceStatistics': False,
            'overwriteExisting': False,
            'dicts': {},
            'usedDicts': {},
            'usedParsers': [],
        }
        resp, _ = self.api.request('project/export', method='post', json={**defaults, **options})

        location = resp.headers.get('location')
        qs = parse_qs(urlparse(location).query)
        export_id = qs['exportId'][0]

        if not wait:
            return export_id

        while True:
            time.sleep(1)
            status = self.get_export_status(export_id)
            # status has only empty state key when the server rebooted during the project export
            if status.get('state') in ('Exported', 'Error'):
                return status

    def get_export_status(self, export_id: str) -> Dict[str, Any]:
        """Get the status of project export

        :param export_id: the export identifier

        .. versionadded:: 0.28.0
        """

        return self.api.get('project/export/status', params={'exportId': export_id})

    def get_nodes(self) -> Nodes:
        """Returns a dictionary of project's nodes information.

        .. deprecated:: 0.15.0
           Use :meth:`Project.get_node_list` instead.
        """
        warnings.warn(
            'Project.get_nodes() is deprecated, use Project.get_node_list() instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        json = self.api.get(
            'project/nodes',
            params={'prjUUID': self.uuid},
            headers={'sid': self.api.sid} if self.api.sid else None,
        )
        return {node.pop('name'): node for node in json['nodes']}

    def get_execution_statistics(self) -> Tuple[Nodes, Dict[str, int]]:
        """Returns the execution statistics for nodes in the project.

        Similar to :meth:`Project.get_nodes` but nodes contains extra information
        and the project statistics.

        .. deprecated:: 0.15.0
           Use :meth:`Project.get_execution_stats` instead.
        """
        warnings.warn(
            'Project.get_execution_statistics() is deprecated, use' 'Project.get_execution_stats() instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        json = self.api.get('project/execution-statistics', params={'prjUUID': self.uuid})
        nodes = {node.pop('name'): node for node in json['nodes']}
        return nodes, json['nodesStatistics']

    def preview(self, node: Union[str, Dict[str, str]]) -> _DataSet:
        """Returns first 1000 rows of data from ``node``, texts and strings are
        cutoff after 250 symbols.

        :param node: node name or dict with name and type of node

        .. deprecated:: 0.16.0
            Use :meth:`Dataset.preview` instead.
        """
        warnings.warn(
            'Project.preview() is deprecated, use Dataset.preview() instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        return self.dataset(node).preview()

    def set_parameters(
        self,
        node: str,
        node_type: str,
        parameters: Dict[str, Any],
        declare_unsync: bool = True,
        hard_update: bool = True,
    ) -> None:
        """
        Set parameters of the selected Parameters node in the project.

        :param node: name of Parameters node
        :param node_type: node type, which parameters need to be set.
        :param parameters: default parameters of the node to be set.
        :param declare_unsync: reset the status of the Parameters node.
        :param hard_update: update every child node with new parameters if True, \
            otherwise reset their statuses. Works only if declare_unsync is True.

        .. deprecated:: 0.18.0
           Use :meth:`Parameters.set` instead.
        """
        warnings.warn(
            'Project.set_parameters() is deprecated, use Project.parameters.set() instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        warns = self.parameters(node).set(node_type, parameters, None, declare_unsync, hard_update)
        if warns:
            for msg in warns:
                warnings.warn(msg)


class Parameters:
    def __init__(self, prj: Project, _id: Optional[str]):
        self._prj = prj
        self._api = prj.api
        self.id = _id

    def get(self):
        """Returns list of nodes with parameters and strategies supported by ``Parameters`` node."""
        return self._api.get('parameters/nodes')

    def set(
        self,
        node_type: str,
        parameters: Union[Dict[str, str], List[Dict[str, str]]],
        strategies: Optional[List[int]] = None,
        declare_unsync: bool = True,
        hard_update: bool = True,
        wait: bool = True,
    ) -> Optional[List[str]]:
        """
        Sets `node_type` parameters and strategies for the Parameters node.

        If `parameters` is the list of dictionaries with parameters then
        /configure-array endpoint is used otherwise /configure.

        :param node_type: node type which parameters needs to be set
        :param parameters: node type parameters
        :param strategies: node type strategies
        :param declare_unsync: reset status of the Parameters node. True by default.
        :param hard_update: update every child node with new parameters if True, \
            otherwise reset their statuses. Works only if declare_unsync is True.\
            True by default.
        :param wait: wait for this node to set parameters for each child node.\
            True by default.
        """

        if strategies is None:
            strategies = []

        method = 'configure-array' if isinstance(parameters, list) else 'configure'

        resp, _warnings = self._api.request(
            f'parameters/{method}',
            method='POST',
            params={'prjUUID': self._prj.uuid, 'obj': self.id},
            json={
                'type': node_type,
                'settings': parameters,
                'strategies': strategies,
                'declareUnsync': declare_unsync,
                'hardUpdate': hard_update,
            },
        )

        query = urlparse(resp.headers.get('location')).query
        try:
            wave_id = int(parse_qs(query).get('executionWave')[0])
        except TypeError:
            pass
        else:
            if wait:
                while self._prj.is_running(wave_id):
                    time.sleep(1)

        return _warnings

    def clear(self, *node_types: List[str], declare_unsync: bool = True) -> Optional[List[str]]:
        """
        Clears parameters and strategies of `node_types` for the Parameters node.
        If `node_types` is empty it clears parameters and strategies of all nodes.

        :param node_types: node types which parameters needs to be cleared
        :param declare_unsync: reset status of the Parameters node
        """
        return self._api.post(
            'parameters/clear',
            params={'prjUUID': self._prj.uuid, 'obj': self.id},
            json={
                'nodes': node_types,
                'declareUnsync': declare_unsync,
            },
        )


def retry_on_invalid_guid(func):
    @functools.wraps(func)
    def wrapper(cls, *args, **kwargs):
        try:
            return func(cls, *args, **kwargs)
        except _WrapperNotFound:
            cls._update_guid()
            return func(cls, *args, **kwargs)

    return wrapper


class DataSet:
    def __init__(self, prj: Project, node: Node):
        self._prj = prj
        self._api = prj.api
        self._node = node
        # on purpose send wrong wrapperGuid(empty string) at first request to /dataset/* endpoints
        # to create dataset wrapper on server and retrieve its' guid by @retry_on_invalid_guid
        self.guid: str = ''
        self._update_guid()  # temporary fix until server starts to return proper error response

    @retry_on_invalid_guid
    def get_info(self) -> Dict[str, Any]:
        """Get information about dataset."""
        return self._api.get('dataset/info', params={'wrapperGuid': self.guid})

    @retry_on_invalid_guid
    def get_progress(self) -> Dict[str, Union[int, str]]:
        """Get dataset progress."""
        return self._api.get('dataset/progress', params={'wrapperGuid': self.guid})

    def preview(self, precision: int = 6, include_blank_cells: bool = False) -> _DataSet:
        """
        Get dataset preview.

        Contains the first 1000 rows, string/text are cut off after 250 symbols.
        By default, numbers are rounded to 6 significant digits and blank cells are omitted.

        :param precision: (optional) number of significant digits. 6 by default.
        :param include_blank_cells: (optional) include blank cells in dataset. False by default.

        :raises: APIException if non-default parameters are used with the old version of server,
            which doesn't support them. In this case retry the method with default parameters.

        .. versionadded:: 0.24.0
            The *precision* and *include_blank_cells* parameters.
        """
        params = {
            'prjUUID': self._prj.uuid,
            'name': self._node['name'],
            'type': self._node['type'],
        }
        if precision != 6:
            params['precision'] = precision
        if include_blank_cells is not False:
            params['writeEmptyValues'] = include_blank_cells

        return self._api.get('dataset/preview', params=params)

    def iter_rows(self, start: int = 0, stop: Optional[int] = None) -> Iterator[Dict[str, JSON_VAL]]:
        """
        Iterate over rows in dataset.

        :param start:
        :param stop:

        :raises: ValueError if `start` or `stop` is out of datasets' row range

        Usage::

          # download first 10 rows
          >>> head = []
          >>> for row in ds.iter_rows(0, 10):
          ...     head.append(row)
          # download full dataset and convert it to pandas.DataFrame
          >>> table = list(ds.iter_rows())
          >>> df = pandas.DataFrame(table)
        """
        info = self.get_info()
        max_row = info['rowCount']
        if stop is None:
            stop = max_row

        # предполагается что если stop определен то пользователь в курсе количества строк в датасете
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
                columns = info.get('columnsInfo') or info['columns']
                for column in columns:
                    if column['flags'].get('getTextAlways'):
                        result[column['title']] = get_text(self.idx, column['id'])
                    # elif column['type'] == 'DateTime':  # todo convert to python datetime?
                    else:
                        _value = rows[self.idx][column['id']]
                        if _value == 1e100:
                            _value = None
                        elif _value == 8e100:
                            _value = math.inf
                        elif _value == -8e100:
                            _value = -math.inf

                        result[column['title']] = _value

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
        return self._api.get(
            'dataset/values',
            json={'wrapperGuid': self.guid, 'rowCount': row_count},
        )

    @retry_on_invalid_guid
    def _cell_text(self, row: int, col: int) -> str:
        return self._api.get(
            'dataset/cell-text',
            json={
                'wrapperGuid': self.guid,
                'row': row,
                'col': col,
            },
        )['text']

    @retry_on_invalid_guid
    def statistics_tab(self, col: int) -> List:
        """This operation returns data on the statistics of the dataset
        
        param col: ID of the column to get statistics for
        """
        return self._api.post('dataset/statistics', json={'wrapperGuid': self.guid, 'columnId': col})
    
    @retry_on_invalid_guid
    def distinct(self, col_id: int, col_name: str = "", col_type: str = "") -> List:
        """This operation returns the GUID of the wrapper table of unique records of the dataset
        
        param col_id: ID of the column for which you need to get a table wrapper of unique records
        param col_name: name of the column
        param col_type: type of the column
        """
        return self._api.post('dataset/distinct', json={'wrapperGuid': self.guid, 'columnId': col_id, 'columnName': col_name, 'columnType': col_type})

    @retry_on_invalid_guid
    def search(self, col_id: int, col_name: str = "", col_type: str = "", search_from: int = 0, search_how: int = 0, str_value: str = "", 
               double_value: float = 0, match_case: bool = False, search_up: bool = False,
               use_regex: bool = False, unique_id: str = "", use_pdl: bool = False) -> List:
        """This operation searches for values in the selected dataset
        
        
        """
        request_body = {
            'wrapperGuid': self.guid, 
            'doubleValue': double_value, 
            'strValue': str_value,
            'columnId': col_id,
            'searchFrom': search_from,
            'searchUp': search_up,
            'columnName': col_name,
            'columnType': col_type,
            'uniqueId': unique_id,
            'searchHow': search_how,
            'matchCase': match_case,
            'useRegEx': use_regex,
            'usePDL': use_pdl
        }
        return self._api.post('dataset/search', json=request_body)
    
    @retry_on_invalid_guid
    def sort_dataset(self, col: list) -> List:
        """This operation sorts the values of a dataset
        
        param col: array of column parameters
        """
        return self._api.post('dataset/sort', json={'wrapperGuid': self.guid, 'columns': col})
    
    @retry_on_invalid_guid
    def filter_dataset(self, action: int, how_search: int, col_id: int = 0, value: int = 0,
                       str_value: str = "", match_case: bool = False, use_regex: bool = False, use_pdl: bool = False, col_name: str = "",
                       col_type: str = "", day: int = 0, month: int = 0, year: int = 0) -> List:
        """This operation filters a dataset by specified values
        
        param col_id: ID of the column to filter
        param action: The way to filter a dataset
        param value: Value to filter a dataset
        param how_search: The way to search a value
        param match_case: Flag to enable case-sensitive filtration
        param use_regex: Flat to use regular expressions to filter
        param use_pdl: Flag to use PDL to filter
        param col_name: Name of the column to filter
        param col_type: Type of the column to filter
        param day: Day value to filter when working with the date/time column
        param month: Month value to filter when working with the date/time column
        param year: Year value to filter when working with the date/time column
        """
        massive = [0, 1, 2, 3, 4, 5]
        if action not in massive or how_search not in massive[:3]:
            raise ValueError("action can accept numbers from 0 to 5, how_search from 0 to 2")
        request_body = {
            'wrapperGuid': self.guid,
            'columnId': col_id,
            'action': action,
            'value': value,
            'strValue': str_value,
            'howsearch': how_search,
            'matchCase': match_case,
            'useRegEx': use_regex,
            'usePDL': use_pdl,
            'columnName': col_name,
            'columnType': col_type,
            'day': day,
            'month': month,
            'year': year
        }
        return self._api.post('dataset/filter', json=request_body)
    
    @retry_on_invalid_guid
    def get_binary(self, key: str, file_name: str = "content"):
        """This operation returns the binary content of the dataset
        
        param key: ID of the column containing binary data
        param file_name: name of the file to be returned
        """
        return self._api.get('dataset/get-binary-content', params={'wrapperGuid': self.guid, 'key': key, 'fileName': file_name})

    @retry_on_invalid_guid
    def dataset_export(self, type: str, file_name: str) -> List:
        """This operation allows you to export a dataset to a file
        
        param type: a file type you want to export your data to ("csv", "xls", "html", "xml", "xlsx", "json")
        param file_name: name of the file
        """
        return self._api.post("dataset/export", json={'wrapperGuid': self.guid, 'type': type, 'fileName': file_name})
    