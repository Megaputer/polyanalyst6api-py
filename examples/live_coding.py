"""
Edit ``Python node``'s code in any editor and instantly view the node output in terminal.
"""
import argparse
import time

import urllib3
import polyanalyst6api

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

server_url = 'https://localhost:5043'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('node', help='The python node name', default='Python')
    parser.add_argument('--project', required=True, help="The polyanalyst's project uuid")
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=False, default='')

    args = parser.parse_args()

    with polyanalyst6api.API(server_url, args.username, args.password) as api:
        prj = api.project(args.project)

        prev_result = None
        while True:
            prj.execute(args.node, wait=True)
            result = prj.dataset(args.node).preview()
            if result != prev_result:
                print(result)
                prev_result = result
            time.sleep(1)
