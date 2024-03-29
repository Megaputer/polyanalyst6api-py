import polyanalyst6api

server_url = ''  # protocol, domain, port : https://www.example.com/ or https://localhost:5043/
username = ''
password = ''
project_id = ''
node_name = ''  # root node name


with polyanalyst6api.API(server_url, username, password) as api:
    prj = api.project(project_id)

    prj.execute(node_name, wait=True)
    prj.save()
