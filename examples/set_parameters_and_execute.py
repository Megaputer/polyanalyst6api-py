"""
The example of set_parameters method usage.

To execute this script you need to:
  1. Create a new project
  2. Add 2 nodes to flowchart: Parameters and Internet Source
  3. Add a link from Parameters to Internet Source
"""
import sys
import time

import polyanalyst6api

server_url = ''
username = ''
password = ''
project_id = ''

URL = 'https://www.megaputer.ru/'


with polyanalyst6api.API(server_url, username, password) as api:

    # the 'parameters/configure' endpoint only works in server versions from 2293 and 2236
    info = api.get_server_info()
    build_version = int(info['build'])
    print(build_version)
    if build_version < 2293 and build_version not in [-1, 2236]:
        sys.exit(
            'The given PolyAnalyst server does not support Setting parameters feature. '
            'Please upgrade to the latest version.'
        )

    prj = api.project(project_id)

    prj.set_parameters('Parameters (1)', 'DataSource/INET', parameters={'URL': URL})
    time.sleep(0.5)

    prj.execute('Internet Source', wait=True)

    assert prj.dataset('Internet Source').preview()[0]['URL'] == URL
