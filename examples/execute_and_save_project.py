import polyanalyst6api as pa

netloc = ''  # protocol, domain, port : https://www.example.com/ or https://localhost:5043/
login = ''
password = ''
project_id = ''
node_name = ''  # root node name


api = pa.API(netloc, login, password)
api.login()
prj = api.project(project_id)

try:
    prj.execute(node_name)
except pa.APIException as exc:
    print(exc)
else:
    # wait for nodes to complete execution
    for node in prj.get_node_list():
        prj.wait_for_completion(node)

    prj.save()
