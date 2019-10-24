0.8.2 (2019-10-23)
==================

Bugfixes
--------

- Update pytus version to 0.2.0. This will fix access denied error when calling `delete_file` method after uploading an empty file. (#2)


Improved Documentation
----------------------

- `upload_file` issues a warning if `file`'s current position is not pointed to the beginning of the file. (#1)
