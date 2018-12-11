import polyanalyst6api as pa

netloc = ''
login = ''
password = ''
project_id = ''


with pa.API(netloc, login, password) as api:
    prj = api.project(project_id)
    nodes_stats = prj.execution_statistics[0]
    for node_name, node_stats in nodes_stats.items():
        print(f"The {node_name} node execution takes {node_stats['duration']} seconds.")
