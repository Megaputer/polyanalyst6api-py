![Build status](https://github.com/Megaputer/polyanalyst6api-py/actions/workflows/ci.yml/badge.svg)
[![PyPI package](https://img.shields.io/pypi/v/polyanalyst6api)](https://pypi.org/project/polyanalyst6api)
[![Downloads](https://static.pepy.tech/badge/polyanalyst6api/month)](https://pepy.tech/project/polyanalyst6api)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/polyanalyst6api)](https://pypi.org/project/polyanalyst6api/)
[![MIT License](https://img.shields.io/github/license/megaputer/polyanalyst6api-py)](https://github.com/Megaputer/polyanalyst6api-py/blob/master/LICENSE)

**_polyanalyst6api_ is a simple and easy to use client library for the PolyAnalyst API.**

This package provides wrappers for PolyAnalyst `Analytical Client`, `Scheduler` and `Drive`.
Using it you can execute nodes, view datasets, run tasks, download/upload files and so on.

## Installation

Python 3.7+ is required. Install and upgrade `polyanalyst6api` with these commands:

```shell
pip install polyanalyst6api
pip install --upgrade polyanalyst6api
```

## Documentation

See [API Reference](https://polyanalyst6api-py.rtfd.io) for the client library methods.

Refer to **PolyAnalyst User Manual** at **Application Programming Interfaces** > **Version 01** for REST API specification.

## Usage

Import an api client and log in to PolyAnalyst server

```python
from polyanalyst6api import API

with API(POLYANALIST_URL, USERNAME, PASSWORD) as api:
    # making a request to PolyAnalyst endpoint that require authorization
    print(api.get_server_info())
```

### Working with project

Instantiate project wrapper by calling with existing project ID:
```python
prj = api.project(PROJECT_UUID)
```

Set `Python` node code using parent `Parameters` node.
```python
prj.parameters('Parameters (1)').set(
    'Dataset/Python',
    {'Script': 'result = pandas.DataFrame([{"val": 42}])'}
)
```

Execute `Python` node and wait to complete execution
```python
prj.execute('Python', wait=True)
```

Check node results:
```python
ds = prj.dataset('Python').preview()
assert ds[0]['val'] == 42
```

Save project:
```python
prj.save()
```

### Downloading file from user home folder using PA Drive API

```python
content = api.drive.download_file('README.txt')
with open(r'C:\README.txt', mode='wb+') as local_file:
    local_file.write(content)
```

See [polyanalyst6api-python/examples](https://github.com/Megaputer/polyanalyst6api-py/tree/master/examples) for more complex examples.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/Megaputer/polyanalyst6api-py/tree/master/LICENSE) file for details
