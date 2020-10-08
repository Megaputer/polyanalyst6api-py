"""
polyanalyst6api.drive
~~~~~~~~~~~~~~~~~~~~~

This module contains functionality for access to PolyAnalyst Drive API.
"""
import os
import pathlib
import warnings
from urllib.parse import urljoin
from typing import Optional, Union, IO

import pytus
from pytus.main import _get_offset, _get_file_size
import requests

from .exceptions import APIException


__all__ = ['Drive']


class Drive:
    def __init__(self, api):
        self.api = api

    def upload(self, source: Union[str, os.PathLike], dest: str = '', recursive: bool = True) -> None:
        """
        Upload file or folder to PolyAnalyst server.

        Pass ``recursive`` as False to just create folder on the server without
        uploading inner files and folders.

        :param source: path to the file or folder
        :param dest: (optional) path to the folder in the PolyAnalyst's user directory
        :param recursive: (optional) upload subdirectories recursively

        :raises: TypeError if ``source`` is not string or path-like object.\
            ValueError if ``source`` does not exists
        """
        if not isinstance(source, (str, os.PathLike)):
            raise TypeError('The source parameter should be either string or path-like object.')

        source = pathlib.Path(source)
        if not source.exists():
            raise ValueError(f"Cannot find '{source}': No such file or directory.")

        def _upload(target: pathlib.Path, dest_dir: str) -> None:
            if target.is_file():
                with target.open(mode='rb') as f:
                    self.api.fs.upload_file(f, name=target.name, path=dest_dir)
            elif target.is_dir():
                try:
                    self.api.fs.create_folder(name=target.name, path=dest_dir)
                except APIException as exc:
                    if 'Folder already exists' in exc.message:
                        pass
                    else:
                        raise

                if recursive:
                    for child in target.iterdir():
                        _upload(child, f'{dest_dir}/{target.name}')

        _upload(source, dest)

    def create_folder(self, name: str, path: str = '') -> None:
        """
        Create a new folder inside the PolyAnalyst's user directory.

        :param name: the folder name
        :param path: a relative path of the folder's parent directory
        """
        self.api.post('folder/create', json={'path': path, 'name': name})

    def delete_folder(self, name: str, path: str = '') -> None:
        """
        Delete the folder in the PolyAnalyst's user directory.

        :param name: the folder name
        :param path: a relative path of the folder's parent directory
        """
        self.api.post('folder/delete', json={'path': path, 'name': name})

    def delete_file(self, name: str, path: str = '') -> None:
        """
        Delete the file in the PolyAnalyst's user directory.

        :param name: the filename
        :param path: a relative path of the file's parent directory
        """
        self.api.post('file/delete', json={'path': path, 'name': name})

    def download_file(self, name: str, path: str = '') -> bytes:
        """
        Download the binary content of the file.

        :param name: the filename
        :param path: a relative path of the file's parent directory
        """
        data = self.api.post('file/download', json={'path': path, 'name': name})
        resp, _ = self.api.request(
            urljoin(self.api.url, '/polyanalyst/download'),
            method='get',
            params={'uid': data['uid']}
        )
        return resp.content

    def upload_file(self, file: IO, name: Optional[str] = None, path: str = '') -> None:
        """
        Upload the file to the PolyAnalyst's user directory.

        .. warning::
            Make sure to create a new file or file-like object for every
            :meth:`Drive.upload_file` call!

        .. note::
           Always prefer :meth:`Drive.upload` over this method.

        :param file: the file or file-like object to upload
        :param name: the filename other than `file`'s name
        :param path: (optional) a relative path of the file's parent directory

        Usage::
          >>> drive = Drive(...)
          >>> with open('CarData.csv', mode='rb') as file:
          ...     drive.upload_file(file, name='cars.csv', path='/data')
        """
        if file.tell():
            warnings.warn(
                "The file object's current position is not at the beginning of the file."
                "This will result in uploading only the part of the file!"
            )

        file_name = name or os.path.basename(file.name)
        file_size = _get_file_size(file)

        file_endpoint, _ = pytus.create(
            urljoin(self.api.url, 'file/upload'),
            file_name,
            file_size,
            session=self.api._s,
            metadata={'foldername': path},
        )

        pytus.resume(file, file_endpoint, session=self.api._s, offset=0)

        # free up resources on the server if file is not uploaded completely
        try:
            offset = _get_offset(file_endpoint, session=self.api._s)
            if file_size != offset:
                pytus.terminate(file_endpoint, session=self.api._s)
        except requests.exceptions.RequestException:
            pass
