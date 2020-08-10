import enum
import time
from typing import Any, Dict, List, Optional, Union

import polyanalyst6api
import pytest
import jsonschema
from pydantic import BaseModel, create_model

URL = 'https://localhost:5043'
USER = 'administrator'
UUID = 'bbd41a95-a45c-4cd6-bb0a-8bc472d04708'

# that the formats of the returned data of the Project methods has not changed
# todo export and use pydantic models to api.py


@pytest.fixture(scope='module')  # todo with module scope tests runs slower
def project():
    api = polyanalyst6api.API(URL, USER)
    api.login()
    return api.project(UUID)


class NodeStatus(str, enum.Enum):
    incomplete = 'incomplete'
    empty = 'empty'
    unsynchronized = 'unsynchronized'
    synchronized = 'synchronized'


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

    time.sleep(.5)  # wait till PA updates node statuses
    task_list = project.get_tasks()

    assert len(task_list) == 1
    assert jsonschema.validate(task_list, TaskList.schema()) is None


@pytest.mark.run('third')
@pytest.mark.vcr
def test_get_execution_statistics(project):
    class Node(BaseModel):
        id: int
        type: str
        # name: str
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

    class NodesStatistics(BaseModel):
        emptyNodesCount: Optional[int]
        synchronizedNodesCount: Optional[int]
        unsynchronizedNodesCount: Optional[int]

    time.sleep(5)  # todo wait only when requesting
    nodes, stats = project.get_execution_statistics()

    assert jsonschema.validate(nodes, create_model('', __root__=Node).schema()) is None
    assert jsonschema.validate(stats, NodesStatistics.schema()) is None


@pytest.mark.vcr
def test_get_nodes(project):
    class Node(BaseModel):
        id: int
        # name: str
        type: str
        status: NodeStatus
        errMsg: Optional[str]

    result = project.get_nodes()
    assert jsonschema.validate(result, create_model('', __root__=Node).schema()) is None


@pytest.mark.vcr
def test_preview(project):
    class Row(BaseModel):
        __root__: Dict[str, Union[str, int, float, bool]]

    class Preview(BaseModel):
        __root__: List[Row]

    assert jsonschema.validate(project.preview('Python'), Preview.schema()) is None


