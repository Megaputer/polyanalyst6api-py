"""
The example of set_parameters method usage.

To execute this script you need to:
  1. Create a new project
  2. Add 2 nodes to flowchart: Parameters and Internet Source (don't change the Parameters node name)
  3. Add link from Parameters to Internet Source
  4. Until T17291 is not fixed the Parameters node should be preconfigured manually:
    - select Internet Source in Parameters Properties
    - set any value on Default column for the URL parameter (the value will be overwritten by this script)
    - click OK
"""
import sys

import polyanalyst6api

server_url = ''
user = ''
password = ''
project_uuid = ''

URL = 'https://www.megaputer.ru/'


with polyanalyst6api.API(server_url, user, password) as api:

    # the 'parameters/configure' endpoint only works in server versions from 2293 and 2236
    info = api.get_server_info()
    build_version = int(info['build'])
    if build_version < 2293 and build_version != 2236:
        sys.exit(f'The given PolyAnalyst server does not support Setting parameters feature. '
                 f'Please upgrade to the latest version.')

    prj = api.project(project_uuid)

    prj.set_parameters(
        'Parameters',
        'DataSource/INET',
        parameters={
            'URL': URL,
        }
    )

    prj.execute('Internet Source', wait=True)

    assert prj.preview('Internet Source')[0]['URL'] == URL
