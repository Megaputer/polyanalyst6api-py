import enum
import time
from typing import Any, Dict, List, Optional, Union

import jsonschema
import pytest
from pydantic import BaseModel

import polyanalyst6api

URL = 'https://localhost:5043'
USER = 'administrator'
UUID = 'bbd41a95-a45c-4cd6-bb0a-8bc472d04708'

# test that the formats of the returned data of the Project methods has not changed


@pytest.fixture(scope='module')  # todo with module scope tests runs slower
def project():
    api = polyanalyst6api.API(URL, USER)
    api.login()
    return api.project(UUID)


# todo export and use pydantic models in api.py
class NodeStatus(str, enum.Enum):
    incomplete = 'incomplete'
    empty = 'empty'
    unsynchronized = 'unsynchronized'
    synchronized = 'synchronized'


class Node(BaseModel):
    id: int
    name: str
    type: str
    status: NodeStatus
    errMsg: Optional[str]


class NodeStatistic(BaseModel):
    id: int
    type: str
    name: str
    status: NodeStatus
    errMsg: Optional[str]
    startTime: int
    endTime: int
    duration: float
    datasetRows: Optional[int]
    datasetCols: Optional[int]
    freeMemoryInitial: int
    freeMemoryFinal: int
    freeDiskInitial: int
    freeDiskFinal: int


@pytest.mark.run('first')
def test_launch_python(project):
    script = '''
import time
time.sleep(5)
result = pandas.DataFrame(data={'col1': [1.1, 2], 'col2': ['text', None]})
    '''
    project.set_parameters('Parameters', 'Dataset/Python', parameters={'Script': script})
    project.execute('Python')
    assert True


@pytest.mark.run('second')
@pytest.mark.vcr
def test_get_tasks(project):
    class Task(BaseModel):
        name: str
        objId: int
        progress: float
        subProgress: int
        currentState: str
        startTime: Any  # should be datetime but ValidationError: datetime.datetime(...) is not of type 'string'
        state: int

    class TaskList(BaseModel):
        __root__: List[Task]

    time.sleep(0.5)  # wait till PA updates node statuses
    task_list = project.get_tasks()

    assert len(task_list) == 1
    assert jsonschema.validate(task_list, TaskList.schema()) is None


@pytest.mark.run('third')
@pytest.mark.vcr
def test_get_execution_statistics(project):
    class _NodeStatistic(NodeStatistic):
        name: Optional[str]  # todo exclude field https://github.com/samuelcolvin/pydantic/issues/830

    class Nodes(BaseModel):
        __root__: Dict[str, _NodeStatistic]

    class Statistics(BaseModel):
        emptyNodesCount: Optional[int]
        synchronizedNodesCount: Optional[int]
        unsynchronizedNodesCount: Optional[int]

    time.sleep(5)  # todo wait only when requesting
    nodes, stats = project.get_execution_statistics()

    assert jsonschema.validate(nodes, Nodes.schema()) is None
    assert jsonschema.validate(stats, Statistics.schema()) is None


@pytest.mark.vcr('test_get_execution_statistics.yaml')
def test_get_execution_statistics_is_deprecated(project):
    with pytest.deprecated_call():
        _ = project.get_execution_statistics()


@pytest.mark.vcr('test_get_nodes.yaml')
def test_get_nodes_is_deprecated(project):
    with pytest.deprecated_call():
        _ = project.get_nodes()


@pytest.mark.vcr
def test_get_nodes(project):
    class _Node(Node):
        name: Optional[str]

    class Nodes(BaseModel):
        __root__: Dict[str, _Node]

    assert jsonschema.validate(project.get_nodes(), Nodes.schema()) is None


@pytest.mark.vcr
def test_preview(project):
    class Row(BaseModel):
        __root__: Dict[str, Union[str, int, float, bool]]

    class Preview(BaseModel):
        __root__: List[Row]

    assert jsonschema.validate(project.preview('Python'), Preview.schema()) is None


@pytest.mark.vcr('test_get_nodes.yaml')
def _test_get_node_list(project):
    class Nodes(BaseModel):
        __root__: List[Node]

    assert jsonschema.validate(project.get_node_list(), Nodes.schema()) is None


@pytest.mark.vcr('test_get_execution_statistics.yaml')
def test_get_execution_stats(project):
    class Stats(BaseModel):
        __root__: List[NodeStatistic]

    assert jsonschema.validate(project.get_execution_stats(), Stats.schema()) is None
