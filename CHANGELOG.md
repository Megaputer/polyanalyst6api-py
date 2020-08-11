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
