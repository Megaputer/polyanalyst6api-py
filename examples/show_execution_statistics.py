import polyanalyst6api as pa

netloc = ''
login = ''
password = ''
project_id = ''


with pa.API(netloc, login, password) as api:
    prj = api.project(project_id)
    stats = prj.get_execution_stats()
    for node in stats:
        print(f"The {node['name']} node execution takes {node['duration']} seconds.")
