0.9.1 (2019-10-25)
==================

Bugfixes
--------

- The client was raising unspecified ClienException when response has 2xx success
  status code but not 200 or 202. Now client's `API.request` method just returns
  a tuple with `requests.Response` instance and `None` when response status code
  neither 200, 202, 403 or 500. (#7)
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

- Update pytus version to 0.2.0. This will fix access denied error when calling `delete_file` method after uploading an empty file. (#2)


Improved Documentation
----------------------

- `upload_file` issues a warning if `file`'s current position is not pointed to the beginning of the file. (#1)
