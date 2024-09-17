import base64
import os
import re
import textwrap
from datetime import datetime, timezone
from pathlib import Path

from github import Github, BadCredentialsException, UnknownObjectException, GithubException

import global_variables as gv
from global_variables import FILES_FILE_PATH, AUTH_FILE_PATH, DOWNLOADED_DIRECTORY_PATH


def return_manual() -> str:
    return textwrap.dedent('''
    Q: How to generate an access token?
    A: Link: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic

    Q: What format of link should i consider when I add a new file?
    A: This is how link should look like: https://github.com/revel111/GithubDownloader/blob/master/main.py

    Q: Where can I report about bugs and send any idea regarding this project?
    A: Link: https://github.com/revel111/GithubDownloader/issues 
    I ask you to report any kind of bugs. Each bug will be fixed and any idea will be reviewed.
    ''')


def parse_link(link) -> tuple[str, str, str, str]:
    pattern = r"https://github\.com/(?P<owner_name>[^/]+)/(?P<repo_name>[^/]+)/blob/(?P<branch>[^/]+)/(?P<path>.+)"
    match = re.match(pattern, link)

    if match:
        return (
            match.group('owner_name'),
            match.group('repo_name'),
            match.group('branch'),
            match.group('path')
        )
    else:
        raise ValueError


def validate_path(path) -> Path:
    if not path.exists() or not path.is_dir():
        path = DOWNLOADED_DIRECTORY_PATH

    return path


def read_credentials() -> str:
    with open(AUTH_FILE_PATH, 'r') as file:
        return file.read()


def read_tracked_files() -> list:
    with open(FILES_FILE_PATH, 'r') as file:
        files = [line.split() for line in file]

    if not files:
        raise FileNotFoundError

    return files


def check_download(owner_name, repo_name, branch, path, location) -> bool:
    location = Path(location)

    if not location.exists():
        return True

    try:
        repo = gv.git.get_repo(f"{owner_name}/{repo_name}")
        commits = repo.get_commits(path=path, sha=branch)

        latest_commit = commits[0]

        commit_date = latest_commit.commit.author.date
    except (UnknownObjectException, GithubException):
        return False
    except ConnectionError:
        return False

    modification_time = os.path.getmtime(location)
    modification_date = datetime.fromtimestamp(modification_time, tz=timezone.utc)

    return commit_date > modification_date


def delete_all_tracked_files() -> None:
    if FILES_FILE_PATH.exists():
        Path.unlink(FILES_FILE_PATH)
        raise gv.SuccessException('All tracked files were deleted.')

    raise gv.WarningException('No files were being tracked.')


def download_file(owner_name, repo_name, branch, path, location) -> None:
    location = Path(location)

    try:
        repo = gv.git.get_repo(f"{owner_name}/{repo_name}")
        content_encoded = repo.get_contents(path, ref=branch).content
    except (UnknownObjectException, GithubException):
        raise gv.ErrorException('Invalid data was passed.')
    except ConnectionError:
        raise gv.WarningException('No connection with Github. Please check your network connection or try again later.')

    content = base64.b64decode(content_encoded).decode('utf-8')
    name = path.split('/')[-1]

    DOWNLOADED_DIRECTORY_PATH.mkdir(exist_ok=True)

    if location.exists() and location.is_dir():
        with open(location / name, 'w') as file:
            file.write(content)
        raise gv.SuccessException(f'File "{path}" was downloaded into "{location}".')
    else:
        with open(DOWNLOADED_DIRECTORY_PATH / name, 'w') as file:
            file.write(content)
        raise gv.InfoException(
            f'Location "{location}" does not exist, file was was downloaded into "{DOWNLOADED_DIRECTORY_PATH}".')


def delete_tracked_file(line_to_delete, name) -> None:
    try:
        with open(FILES_FILE_PATH, 'r+') as file:
            flag = False
            lines = file.readlines()
            file.seek(0)

            if len(lines) == 0:
                raise FileNotFoundError

            for line in lines:
                if ''.join(line.strip('\n').split(' ')[:-1]) != line_to_delete:
                    file.write(line)
                else:
                    flag = True

            file.truncate()

            if flag:
                raise gv.SuccessException(f'File "{name}" was deleted.')
            else:
                raise gv.ErrorException(f'File "{name}" does not exist.')
    except FileNotFoundError:
        raise gv.WarningException('No files are currently being tracked.')


def authenticate_token(token) -> None:
    try:
        gv.git = Github(token)
        gv.git.get_user().login
    except BadCredentialsException:
        raise gv.ErrorException('You entered invalid secure token. Try again.\n')
    except ConnectionError:
        raise gv.WarningException('No connection with Github. Please check your network connection or try again later.')

    gv.FILES_DIRECTORY_PATH.mkdir(exist_ok=True)
    with open(AUTH_FILE_PATH, 'w') as file:
        file.write(token)


def validate_data(owner_name, repo_name, branch, path) -> None:
    try:
        try:
            gv.git.get_user(owner_name)
        except UnknownObjectException:
            raise gv.ErrorException(f'The user "{owner_name}" does not exist.')

        try:
            repo = gv.git.get_repo(f"{owner_name}/{repo_name}")
        except UnknownObjectException:
            raise gv.ErrorException(f'The repository "{repo_name}" does not exist.')

        try:
            repo.get_branch(branch)
        except GithubException:
            raise gv.ErrorException(f'The branch "{branch}" does not exist in the repository "{repo_name}".')

        try:
            repo.get_contents(path, ref=branch)
        except UnknownObjectException:
            raise gv.ErrorException(f'The file "{path}" does not exist in the branch "{branch}".')
    except ConnectionError:
        raise gv.WarningException('No connection with Github. Please check your network connection or try again later.')
