"""
Edit ``Python node``'s code in any editor and instantly view the node output in terminal.
"""
import argparse
import time

import urllib3
import polyanalyst6api as pa

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = 'https://localhost:5043'


def execute(node, prj):
    prj.execute(node)
    prj.wait_for_completion(node)
    return prj.preview(node)


def main(node, uuid, username, password):
    with pa.API(URL, username, password) as api:
        prj = api.project(uuid)

        prev_result = execute(node, prj)
        while True:
            result = execute(node, prj)
            if result != prev_result:
                print(result)
                prev_result = result
            time.sleep(1.0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('node', help='The python node name', default='Python')
    parser.add_argument('--project', required=True, help="The polyanalyst's project uuid")
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=False, default='')

    args = parser.parse_args()
    main(args.node, args.project, args.username, args.password)
