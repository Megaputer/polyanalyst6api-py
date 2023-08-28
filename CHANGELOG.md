0.29.4 (2023-08-28)
===================

No significant changes.


0.29.3 (2023-08-28)
===================

No significant changes.


0.29.2 (2023-08-28)
===================

### Bugfixes

- Fixed APIExceptions are suppressed in `Project.get_execution_stats` method (exec_stats)


0.29.1 (2023-08-19)
===================

### Bugfixes

- Fixed possible issue with using os.PathLike args(replaced str with os.fspath) (fspath)


0.29.0 (2023-08-18)
===================

### Features

- Added support of os.PathLike object in import_project and Drive methods (#7)


0.28.0 (2023-08-18)
===================

### Features

- Added support for exporting a project to the file system (export)

### Deprecations and Removals

- Dropped support of python 3.6 (#2)


0.27.0 (2023-07-27)
===================

### Features

- Turned ssl verification on by default. Added possibility to disable it for tests through passing `verify=False` to `API` call (sslon)

### Bugfixes

- Fixed ssl verification setting is not applied to pytus library (drive)

### Deprecations and Removals

- Removed `certfile` attribute and `version` argument of `API` class because of no longer use (certfile)


0.26.25 (2023-07-19)
====================

Bugfixes
--------

- Fixed 'Not Found for url' error when version arg is None (version)

Deprecations and Removals
-------------------------

- Removed an option to set API version in `API` class. The client now works only with `1.0` API version. (apiversion)
- Deprecated the use of credential file (cred file)

0.26.2 (2023-07-03)
===================

Features
--------

- Added request retries to `project.unload` method to mitigate PABusy error

Bugfixes
--------

- Fixed typos and other minor errors

0.26.0 (2023-05-18)
===================

Features
--------

- Added PABusy exception that is raised on HTTP 503 status code

0.25.1 (2023-04-19)
===================

Bugfixes
--------

- Fixed iter_rows missing `columnsInfo` key in newer versions of PolyAnalyst

0.25.0 (2022-11-15)
===================

Features
--------

- Added optional `skip_hidden` parameter to `project.get_execution_stats` method. (T35030)


0.24.0 (2022-06-16)
===================

Features
--------

- Added ability to import project from file on local file system (T24481) (import)
- Added optional `precision` and `include_blank_cells` parameters to `project.preview` method. (T28860, T28109) (preview)


0.23.0 (2021-09-20)
===================

Features
--------

- Added support of the configuration file (T28739)
- Introduced deprecated earlier `wait_for_completion` method back. Added new `wave_id` argument (T28740)
- Better api error message formatting. For example, "APIException: . Message: 'JSON value is not an array' (500, ...)" -> "APIException: JSON value is not an array (500, ...)" (#1)


Bugfixes
--------

- Fixed deprecated get_parameters raises `TypeError: __init__() takes 3 positional arguments but 4 were given` (#1)
- Fixed deprecated set_parameters method raises `JSON value is not an array` error (#2)


0.22.1 (2021-09-02)
===================

Bugfixes
--------

- Fixed iter_rows method returns 1e+100 and 8e+100 instead of None and inf respectively


0.22.0 (2021-04-27)
===================

Features
--------

- Added the ability to wait for Parameters node to set parameters


0.21.0 (2021-04-26)
===================

Features
--------

- Added additional argument checks to some `Drive` methods
- Added stream download option to `Drive.download_file`


0.20.1 (2021-04-06)
===================

Bugfixes
--------

- Fixed iter_rows method raises ClientException: ('Connection aborted.', ConnectionResetError(10054, 'An existing connection was forcibly closed by the remote host')) when running from different machine

0.20.0 (2020-12-15)
===================

Features
--------

- Added Bearer authentication support (T23887)


0.19.0 (2020-11-05)
===================

Features
--------

- Implemented method for new endpoint /configure-array to set array of parameters (T22774)
- Added the ability to set strategies in Parameters nodes (T23048)


Improved Documentation
----------------------

- Updated documentation for Parameters methods (#1)


0.18.1 (2020-10-21)
===================

Bugfixes
--------

- Fixed locking of empty files by PolyAnalyst

0.18.0 (2020-10-08)
===================

Features
--------

- Added `logout` method and logging out current user when exiting `API` context (#1)
- Added `API.drive` attribute to work with `PolyAnalyst Drive` (#2)
- Added new `Project.parameters` with `get` and `set` methods (#4)
- Added new `Parameters.clear` method to reset parameters of particular node type (#5)


Improved Documentation
----------------------

- Fixed method documentation lengths (#7)


Deprecations and Removals
-------------------------

- Deprecated `API.fs` and `RemoteFileSystem` in favor of `API.drive` and `Drive`, respectively (#3)
- Deprecated `API.get_parameters` and `Project.set_parameters` methods (#6)


0.17.0 (2020-09-22)
===================

Features
--------

- Added new method Project.is_running (T22411)
- Changed Project.execute() to return execution wave identifier (T22411)


Deprecations and Removals
-------------------------

- Deprecated Project.wait_for_completion() in favor of Project.is_running() (#1)


Improved Documentation
----------------------

- Documented Dataset methods in API Reference (#2)
- Fixed links to methods in documentation (#3)


0.16.0 (2020-09-21)
===================

Features
--------

- Added functionality to view properties and full texts of datasets (T21517)


Deprecations and Removals
-------------------------

- Deprecated Project.preview() in favor of Project.dataset().preview() (#1)


0.15.0 (2020-08-11)
===================

Features
--------

- Added support for working with nodes with the same names  (T21997)

Deprecations and Removals
-------------------------

- Deprecated Project.get_nodes() and Project.get_execution_statistics() methods
- Removed private Project._nodes attribute


0.14.0 (2020-07-24)
===================

Features
--------

- Added new hard_update argument to set_parameters method (T19988)


Bugfixes
--------

- Fixed "[WinError 10054] An existing connection was forcibly closed by the remote host" caused by requests to not implemented /logout endpoint


0.13.0 (2020-03-12)
===================

Features
--------

- Added the ability to reset Parameters node status (T19556)


0.12.1 (2020-02-11)
===================

Bugfixes
--------

- Fixed APIs context manager raises APIException when the server doesn't support /logout endpoint (#14)


0.12.0 (2020-01-20)
===================

Features
--------

- Added `logout` method. Implemented logout of current user when `API` context exited if this endpoint supported by server. (#13)


0.11.0 (2019-11-16)
===================

Features
--------

- Add `get_parameters` method to `polyanalyst.API` class for retrieving list of nodes supported by `Parameters` node. Each node info contains its name, type and detailed list of parameters. (#12)


0.10.1 (2019-11-07)
===================

Bugfixes
--------

- Fixed some errors in error handling method (#11)


0.10.0 (2019-11-07)
==================

Features
--------

- Added handling of new error response format (#10)


0.9.2 (2019-10-29)
==================

Bugfixes
--------

- Changed requests methods of RemoteFileSystem functions to correct ones as specified in the API documentation (#9)


0.9.1 (2019-10-25)
==================

Bugfixes
--------

- The client was raising unspecified ClienException when response has 2xx success
  status code other than 200 or 202. Now client's `API.request` method just returns
  a tuple of `requests.Response` and `None` when response status code neither of
  200, 202, 403 or 500. (#7)
- Fixed can't delete file from the server after calling upload_file two and more times with the same file object (#8)


Improved Documentation
----------------------

- Document RemoteFileSystem class methods (#4)
- Fix sphinx cross-reference links (#5)
- Remove repetition of `optional` word (#6)


0.9.0 (2019-10-24)
==================

Features
--------

- Add `upload` method to `RemoteFileSysem` class which encapsulates bare api level `upload_file` and `upload_folder` methods (#3)


0.8.2 (2019-10-23)
==================

Bugfixes
--------

- Fix access denied error when calling `delete_file` method after uploading an empty file. (#2)


Improved Documentation
----------------------

- `upload_file` issues a warning when `file`'s current position is not pointed to the beginning of the file. (#1)
