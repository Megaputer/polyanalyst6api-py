# [WIP]polyanalyst6api-python

`polyanalyst6api-python` is a python package for accessing Polyanalyst's APIs.

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

### Authentication

Import client, initialize it and log in to PolyAnalyst's server:

```python
from polyanalyst6api import ClientSession

client = ClientSession(NETLOC, USERNAME, PASSWORD)
client.login()
```

`ClientSession` supports Context Manager protocol, so you could use it with `with` statement. In this case `ClientSession` will automatically log in with provided credentials.

```python
with pa.ClientSession(NETLOC, USERNAME, PASSWORD) as client:
    pass
```

### Examples

See [polyanalyst6api-python/examples](https://github.com/Megaputer/polyanalyst6api-python/tree/master/examples) for a more complex examples.

At first you need to connect to existing project:
```python
prj = client.project(PROJECT_ID)
```

Show list of nodes in the project:
```python
for node_name in prj.nodes:
    print(node_name)
```

Execute node:
```python
prj.execute(NODE_NAME)
```

Display the truncated result of node execution:
```python
result = prj.preview(NODE_NAME)
print(result)
```

Save the project:
```python
prj.save()
```


Full API specification is stored in the **PolyAnalyst User Manual** under the url below:

```
/polyanalyst/help/eng/24_Application_Programming_Interfaces/toc.html
```

## Supported Python version

`polyanalyst6api-python` works only with `python3` (3.4+).

## License

This project is licensed under the MIT License - see the LICENSE.md file for details
