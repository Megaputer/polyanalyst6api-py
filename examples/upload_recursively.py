import pathlib
import sys

import polyanalyst6api as pa

polyanalyst_url = ''
user = ''
password = ''

local_source = r'D:\Examples'
r"""
>tree /f D:\Examples
D:\EXAMPLES
│   BasketData.csv
│   CarData.csv
└───xmls
        batch1.xml
        batch2.xml
"""
server_dest = ''  # root folder
remove_dest_after_upload = True


def upload(target: pathlib.Path, dest_dir: str):
    if target.is_file():
        print(f'uploading file {target.name} to the {dest_dir}')
        with target.open(mode='rb') as f:
            api.fs.upload_file(f, name=target.name, path=dest_dir)
    elif target.is_dir():
        print(f'creating folder {target.name} in the {dest_dir}')
        try:
            api.fs.create_folder(name=target.name, path=dest_dir)
        except pa.APIException as exc:
            if 'Folder already exists' in exc.message:
                pass
            else:
                raise

        for child in target.iterdir():
            upload(child, f'{dest_dir}/{target.name}')
    else:
        pass


with pa.API(polyanalyst_url, user, password) as api:
    source = pathlib.Path(local_source)
    if not source.exists():
        sys.exit('The `local_source` does not exists')

    upload(source, server_dest)

    if remove_dest_after_upload:
        # currently PolyAnalyst removes only records from its database
        # The folder and files in user home folder will not be deleted
        api.fs.delete_folder(source.name, server_dest)
