import os.path
from datetime import datetime
from pathlib import Path

import requests
from github import Github, Auth, BadCredentialsException

AUTH_DIRECTORY_PATH = Path(__file__).parent.resolve() / 'auth'
AUTH_FILE_PATH = AUTH_DIRECTORY_PATH / 'credentials.txt'
GITHUB_PREFIX = 'https://github.com'
git = Github()


def get_last_commit_date(repo_url, file_path) -> datetime:
    owner, repo_name = repo_url.split('/')[-2:]

    repo = git.get_repo(owner + '/' + repo_name)
    commits = repo.get_commits(path=file_path)

    return commits[0].commit.committer.date


def download_file() -> None:
    response = requests.get('https://github.com/a2x/cs2-dumper/raw/main/output/offsets.cs')
    with open('offsets.cs', 'wb') as file:
        file.write(response.content)


def check_download(file_path) -> None:
    commit_date = get_last_commit_date('https://github.com/a2x/cs2-dumper', 'output/offsets.cs')
    date_updated = None

    if os.path.exists(file_path):
        date_updated = datetime.fromtimestamp(os.path.getmtime(file_path))

    if date_updated is None or date_updated < commit_date:
        download_file()


def authenticate_token() -> None:
    token = str()
    while True:
        token = input('Enter your secure token: ')

        try:
            git = Github(token)
            print('Authentication is successful.\n'
                  'Your login is: ' + git.get_user().login)
            break
        except BadCredentialsException:
            print('You entered invalid secure token. Try again.\n')

    create_credentials(token)


def create_credentials(token) -> None:
    AUTH_DIRECTORY_PATH.mkdir(exist_ok=True)

    with open(AUTH_FILE_PATH, 'w') as file:
        file.write(token)


def read_credentials() -> str:
    with open(AUTH_FILE_PATH, 'r') as file:
        return file.read()


def add_tracked_file() -> None:
    repo_url = input('Enter a full url of a file you want to track.')
    owner, repo_name = repo_url.split('/')[-2:]
    repo = git.get_repo(owner + '/' + repo_name)


def main_menu() -> None:
    if not AUTH_FILE_PATH.exists():
        authenticate_token()
    else:
        try:
            git = Github(read_credentials())
        except BadCredentialsException:
            authenticate_token()

    while True:
        ch = input('Type 1 if you want to change credentials.\n'
                   'Type 2 to show all tracked files.\n'
                   'Type 3 to add a new tracked file.\n'
                   'Type 4 to immediately update all files.\n'
                   'Type 0 to exit.\n')
        match ch:
            case '1':
                authenticate_token()
            case '3':
                add_tracked_file()
            case '0':
                return


if __name__ == '__main__':
    # commit_date = get_last_commit_date('https://github.com/a2x/cs2-dumper', 'output/offsets.cs')
    # check_download('idk')
    main_menu()
    # print(read_credentials())