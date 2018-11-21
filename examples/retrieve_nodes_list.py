import sys

import polyanalyst6api

netloc = ''
login = ''
password = ''
project_id = ''


def main():
    session = polyanalyst6api.ClientSession(netloc, login, password)

    # print error message and exit with 1 error code if login and password don't match
    try:
        session.login()
    except polyanalyst6api.AuthException as exc:
        print(exc)
        sys.exit(1)

    prj = session.project(project_id)
    print(prj.nodes)


if __name__ == '__main__':
    main()
