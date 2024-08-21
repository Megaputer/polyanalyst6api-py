"""
polyanalyst6api.drive
~~~~~~~~~~~~~~~~~~~~~

This module contains functionality for access to PolyAnalyst Drive API.
"""
import os
import pathlib
import warnings
from urllib.parse import urljoin
from typing import Optional, Union, IO, List

import pytus
from pytus.main import _get_offset, _get_file_size
import requests

from .exceptions import APIException, ClientException


__all__ = ['Drive']


class Drive:
    def __init__(self, api):
        self._api = api

    def upload(self, source: Union[str, os.PathLike], dest: str = '', recursive: bool = True) -> None:
        """
        Upload file or folder to PolyAnalyst server.

        Pass ``recursive`` as False to just create folder on the server without
        uploading inner files and folders.

        :param source: path to the local file or folder
        :param dest: (optional) path to the folder in the PolyAnalyst's user directory
        :param recursive: (optional) upload subdirectories recursively

        :raises: TypeError if ``source`` is not string or path-like object.\
            ValueError if ``source`` does not exist
        """
        if not isinstance(source, (str, os.PathLike)):
            raise TypeError('The source parameter should be either string or path-like object.')

        source = pathlib.Path(source)
        if not source.exists():
            raise ValueError(f"Cannot find '{source}': No such file or directory.")

        def _upload(target: pathlib.Path, dest_dir: str) -> None:
            if target.is_file():
                with target.open(mode='rb') as f:
                    self.upload_file(f, name=target.name, path=dest_dir)
            elif target.is_dir():
                try:
                    self.create_folder(name=target.name, path=dest_dir)
                except APIException as exc:
                    if 'Folder already exists' in exc.message:
                        pass
                    else:
                        raise

                if recursive:
                    for child in target.iterdir():
                        _upload(child, f'{dest_dir}/{target.name}')

        _upload(source, dest)

    def list(self, path: str = '/', mask: str = '|*.*') -> List:
        """
        Get a list of files and subdirectories in the PolyAnalyst's user directory.

        :param path: a relative path from user's home folder
        :param mask: a file name and mask divided by ``|``. For example, ``|*.*`` - get all(by default), or ``|.ps6|README.txt``
        :return: a list of dictionaries with 'name', 'lastModified' and 'size'(only for files) values

        .. versionadded:: 0.36.0
        """
        return self._api.get('folder/list', json={'path': os.fspath(path), 'mask': mask})['items']

    def create_folder(self, name: str, path: Union[str, os.PathLike] = '') -> None:
        """
        Create a new folder inside the PolyAnalyst's user directory.

        :param name: the folder name
        :param path: a relative path of the folder's parent directory
        """
        self._api.post('folder/create', json={'path': os.fspath(path), 'name': name})

    def delete_folder(self, name: str, path: Union[str, os.PathLike] = '') -> None:
        """
        Delete the folder in the PolyAnalyst's user directory.

        :param name: the folder name
        :param path: a relative path of the folder's parent directory
        """
        self._api.post('folder/delete', json={'path': os.fspath(path), 'name': name})

    def delete_file(self, name: str, path: Union[str, os.PathLike] = '') -> None:
        """
        Delete the file in the PolyAnalyst's user directory.

        :param name: the filename
        :param path: a relative path of the file's parent directory
        """
        self._api.post('file/delete', json={'path': os.fspath(path), 'name': name})

    def download_file(self, name: str, path: Union[str, os.PathLike] = '', dest: Optional[IO] = None) -> bytes:
        """
        Download the binary content of the file to memory or stream to local file.

        :param name: the filename
        :param path: a relative path of the file's parent directory
        :param dest: the file or file-like object to write drive's file content

        Usage::
          >>> file_content = api.drive.download_file(name='cars.csv', path='/data')
          # The method call above downloads the whole file body into memory. If you're
          # planning on downloading big file (more than 100 megabyte sized file),
          # consider using the streaming download shown below.
          >>> with open('local_file_that_doesnt_exist_yet.csv', 'wb+') as file:
          ...     api.drive.download_file(name='cars.csv', path='/data', dest=file)
        """
        data = self._api.post('file/download', json={'path': os.fspath(path), 'name': name})
        resp, _ = self._api.request(
            'download',
            method='get',
            params={'uid': data['uid']},
            stream=dest is not None,
        )
        if not dest:
            return resp.content

        try:
            for chunk in resp.iter_content(chunk_size=8192):
                dest.write(chunk)
        except AttributeError as exc:
            raise ClientException('`dest` argument should be file or file-like object') from exc

    def upload_file(self, file: IO, name: Optional[str] = None, path: Union[str, os.PathLike] = '') -> None:
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
        try:
            if file.tell():
                warnings.warn(
                    "The file object's current position is not at the beginning of the file."
                    "This will result in uploading only the part of the file!"
                )

            file_name = name or os.path.basename(file.name)
            file_size = _get_file_size(file)
        except AttributeError as exc:
            raise ClientException('`file` argument should be file or file-like object') from exc

        api_session = self._api._s

        file_endpoint, _ = pytus.create(
            urljoin(self._api.url, 'file/upload'),
            file_name,
            file_size,
            session=api_session,
            metadata={'foldername': os.fspath(path)},
        )

        pytus.resume(file, file_endpoint, session=api_session, offset=0)

        # free up resources on the server if file is not uploaded completely
        try:
            offset = _get_offset(file_endpoint, session=api_session)
            if file_size != offset or file_size == 0:
                pytus.terminate(file_endpoint, session=api_session)
        except requests.exceptions.RequestException:
            pass
