"""
polyanalyst6api.project
~~~~~~~~~~~~~~~~~~~~~~~

This module contains functionality for access to PolyAnalyst Analytical Client API.
"""
import datetime
import functools
import math
import time
import warnings
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict, List, Union, Optional, Tuple, Iterator

from .exceptions import APIException, _WrapperNotFound, PABusy

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
    """

    def __repr__(self):
        return f'<Project [{self.uuid}]>'

    def __init__(self, api, uuid: str):
        self.api = api
        self.uuid = uuid
        self._node_list: List[Node] = []

    def get_node_list(self) -> List[Node]:
        """Returns a list of project nodes.

        .. versionadded:: 0.15.0
        """
        return self.api.get('project/nodes', params={'prjUUID': self.uuid})['nodes']

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
            params['skipHiddenNodes'] = 'true' if skip_hidden else 'false'
        try:
            return self.api.get('project/execution-statistics', params=params)['nodes']
        except APIException as exc:
            if 'redundant parameter in query' in str(exc):
                raise APIException(
                    "Current PolyAnalyst server doesn't support `skip_hidden` parameter, try again without it."
                )

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

    def abort(self) -> None:
        """Aborts the execution of all nodes in the project."""
        self.api.post('project/global-abort', json={'prjUUID': self.uuid})

    def execute(self, *args: Union[str, Dict[str, str]], wait: bool = False) -> Optional[int]:
        """
        Initiates execution of nodes and returns execution wave identifier.

        :param args: node names and/or dicts with name and type of nodes
        :param wait: wait for nodes execution to complete

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
        nodes = []
        for arg in args:
            node = self._find_node(arg)
            nodes.append({'name': node['name'], 'type': node['type']})

        resp, _ = self.api.request(
            'project/execute',
            method='post',
            json={'prjUUID': self.uuid, 'nodes': nodes},
        )

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

            while self.is_running(wave_id):
                time.sleep(1)

        return wave_id

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

    def unload(self) -> None:
        """
        Unload the project from the memory.

        From version `0.26.2` this function ensures that the project is unloaded despite PABusy error
        by repeating requests (maximum 10) until PA either returns an ok response or
        returns an error 'the project has not been opened', which means project is also unloaded.

        :raises: PABusy if PABusy returned for all 10 request attempts
        :raises: APIException if the project has been unloaded before this function was called
        """
        for n in range(10):
            try:
                self.api.post('project/unload', json={'prjUUID': self.uuid})
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
