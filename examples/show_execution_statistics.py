import polyanalyst6api

server_url = ''
username = ''
password = ''
project_id = ''


with polyanalyst6api.API(server_url, username, password) as api:
    prj = api.project(project_id)

    for node in prj.get_execution_stats():
        print(f"{node['name']} node took {node['duration']} seconds to execute.")
