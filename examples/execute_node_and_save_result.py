import time

from polyanalyst6api import ClientSession, APIException

netloc = ''  # protocol, domain, port : https://www.example.com/ or https://localhost:5043/
login = ''
password = ''
project_id = ''
node_name = ''


def main():
    with ClientSession(netloc, login, password) as session:
        prj = session.project(project_id)

        # print exception message if node execution raises exception otherwise save project
        try:
            prj.execute(node_name)
        except APIException as exc:
            print(exc)
        else:
            # wait for node completion
            while True:
                node = prj.nodes[node_name]
                if node['status'] == 'synchronized' or node.get('errMsg'):
                    break
                time.sleep(1)

            prj.save()


if __name__ == '__main__':
    main()
