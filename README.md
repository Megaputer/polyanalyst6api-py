# polyanalyst6api

[![PyPI package](https://img.shields.io/pypi/v/polyanalyst6api.svg?)](https://pypi.org/project/polyanalyst6api)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/polyanalyst6api.svg?)](https://pypi.org/project/polyanalyst6api/)
[![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/Megaputer/polyanalyst6api-python/blob/master/LICENSE)

`polyanalyst6api` is a Python library for interacting with PolyAnalyst APIs.

## Installation

Python 3.6+ is required. Install, upgrade and uninstall `polyanalyst6api-python` with these commands:

```
$ pip install polyanalyst6api
$ pip install --upgrade polyanalyst6api
$ pip uninstall polyanalyst6api
```

## Usage

See [API Reference](https://megaputer.github.io/polyanalyst6api-python/) for more detailed information.

### Authentication

Import client, initialize it and log in to PolyAnalyst's server:

```python
import polyanalyst6api as polyanalyst

api = polyanalyst.API(POLYANALIST_URL, USERNAME, PASSWORD)
api.login()
```

`API` supports Context Manager protocol, so you could use it with `with` statement. In this case `API` will automatically log in with provided credentials.

```python
with polyanalyst.API(POLYANALIST_URL, USERNAME, PASSWORD) as api:
    pass
```

### Working with project

See [polyanalyst6api-python/examples](https://github.com/Megaputer/polyanalyst6api-python/tree/master/examples) for a more complex examples.

At first you need to connect to existing project:
```python
prj = api.project(PROJECT_UUID)
```

Print node names within project:
```python
for node_name in prj.get_nodes():
    print(node_name)
```

Initiate node execution:
```python
prj.execute(NODE_NAME)
```

Display the preview of node results:
```python
result = prj.preview(NODE_NAME)
print(result)
```

Save project:
```python
prj.save()
```

## PolyAnalyst API
Full API specification is stored in the **PolyAnalyst User Manual** under the url below:

```
/polyanalyst/help/eng/24_Application_Programming_Interfaces/toc.html
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
