[![PyPI package](https://img.shields.io/pypi/v/polyanalyst6api)](https://pypi.org/project/polyanalyst6api)
[![Downloads](https://static.pepy.tech/badge/polyanalyst6api)](https://pepy.tech/project/polyanalyst6api)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/polyanalyst6api)](https://pypi.org/project/polyanalyst6api/)
[![MIT License](https://img.shields.io/github/license/megaputer/polyanalyst6api-py)](https://github.com/Megaputer/polyanalyst6api-py/blob/master/LICENSE)

**_polyanalyst6api_ is a simple and easy to use client library for the PolyAnalyst API.**

This package provides wrappers for PolyAnalyst `Analytical Client`, `Scheduler` and `Drive`.
Using it you can execute nodes, view datasets, run tasks, download/upload files and so on.

## Installation

Python 3.6+ is required. Install and upgrade `polyanalyst6api` with these commands:

```shell
pip install polyanalyst6api
pip install --upgrade polyanalyst6api
```

## Documentation

See [API Reference](https://megaputer.github.io/polyanalyst6api-py) for the client library methods.

Refer to **PolyAnalyst User Manual** at **Application Programming Interfaces** > **Version 01** for REST API specification.

## Usage

### Authentication

From version `0.23.0` you can use the configuration file to store your credentials. By default, its location is
`C:\Users\_user_\.polyanalyst6api\config` (`~/.polyanalyst6api/config` in linux).

At a minimum, the credentials file should specify the url and credentials keys. You may also want to add a `ldap_server`
if you're logging in via LDAP. All other keys or sections except `DEFAULT` are ignored.

```ini
[DEFAULT]
url=POLYANALYST_URL
username=YOUR_USERNAME
password=YOUR_PASSWORD
ldap_server=LDAP
```

After creating the configuration file you can use `API` context manager to automatically log in to and log out
from PolyAnalyst server:

```python
with polyanalyst6api.API() as api:
    ...
```

Alternatively, you can pass an url, credentials and ldap_server when creating api client. In this case arguments
will be used over values from the configuration file.
```python
with polyanalyst6api.API(POLYANALIST_URL, YOUR_USERNAME, YOUR_PASSWORD) as api:
    ...
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
