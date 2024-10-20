[![Telegram Group](https://img.shields.io/badge/support-join-blue?logo=telegram)](https://t.me/+_AdHkBRnul4xZTg6)
[![PyPI package](https://img.shields.io/pypi/v/polyanalyst6api)](https://pypi.org/project/polyanalyst6api)
[![Downloads](https://static.pepy.tech/badge/polyanalyst6api/month)](https://pepy.tech/project/polyanalyst6api)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/polyanalyst6api)](https://pypi.org/project/polyanalyst6api/)
[![MIT License](https://img.shields.io/github/license/megaputer/polyanalyst6api-py)](https://github.com/Megaputer/polyanalyst6api-py/blob/master/LICENSE)

Welcome to the official Python client library for the PolyAnalyst REST API.

This package provides python wrappers for PolyAnalyst applications, such as *Analytical Client*, *Scheduler*, *Drive*.
Using `polyanalyst6api` you can access and edit projects, publications, files and more.

## Installation

```shell
pip install -u polyanalyst6api
```
> Python 3.7 or later is required.

## Documentation

See [API Reference](https://polyanalyst6api-py.rtfd.io) for the client library methods.

Refer to PolyAnalyst's **User Manual** at **Application Programming Interfaces** > **Version 1** for REST API specification.

## Usage

Import and initialize a client:
```python
from polyanalyst6api import API

# using an api token
client = API(<POLYANALIST_URL>, token=<API_TOKEN>)

# or using PolyAnalyst user credentials. Note that in this case you need to call .login()
client = API(<POLYANALIST_URL>, <USERNAME>, <PASSWORD>)
client.login()
```

Request data using client methods:

```python
>>> prj = client.project(<prjUUID>)
>>> prj.status()
{'status': 'Loaded'}

>>> prj.get_node_list()
[{'id': 11,
  'name': 'Internet Source',
  'status': 'synchronized',
  'subtype': 'INET',
  'type': 'DataSource'},
 {'id': 12,
  'name': 'Python',
  'status': 'synchronized',
  'subtype': 'Python',
  'type': 'Dataset'}]
```

View the [examples](https://github.com/Megaputer/polyanalyst6api-py/tree/master/examples) directory for more code snippets.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/Megaputer/polyanalyst6api-py/tree/master/LICENSE) file for details
