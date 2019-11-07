# polyanalyst6api

`polyanalyst6api` is a python package for accessing PolyAnalyst's APIs.

## Installation

The easiest way to install `polyanalyst6api-python` is from [PyPI](https://pypi.org/project/polyanalyst6api/):

```
$ pip install polyanalyst6api
```

You may also use Git to clone the repository from GitHub and install it manually:

```
git clone https://github.com/Megaputer/polyanalyst6api-python.git
cd polyanalyst6api-python
pip install poetry
poetry install
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

## Supported Python version

`polyanalyst6api-python` works only with `python3` (3.6+).

## License

This project is licensed under the MIT License - see the LICENSE.md file for details
