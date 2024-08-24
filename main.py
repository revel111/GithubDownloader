import base64
import os.path
from datetime import datetime, timezone
from multiprocessing.synchronize import Event
from pathlib import Path
import textwrap
import threading
from threading import Thread
import re

from github import Github, BadCredentialsException, UnknownObjectException, GithubException
from requests.exceptions import ConnectionError

CURRENT_FILE_PATH = Path(__file__).parent.resolve()
AUTH_DIRECTORY_PATH = CURRENT_FILE_PATH / 'auth'
AUTH_FILE_PATH = AUTH_DIRECTORY_PATH / 'credentials.txt'
FILES_DIRECTORY_PATH = CURRENT_FILE_PATH / 'data'
FILES_FILE_PATH = FILES_DIRECTORY_PATH / 'files.txt'
DOWNLOADED_DIRECTORY_PATH = CURRENT_FILE_PATH / 'downloaded'
git = Github()


def download_file(owner_name, repo_name, branch, path) -> None:
    try:
        repo = git.get_repo(f"{owner_name}/{repo_name}")
        content_encoded = repo.get_contents(path, ref=branch).content
    except (UnknownObjectException, GithubException):
        print('Invalid data was passed.')
        return
    except ConnectionError:
        print('No connection with Github. Please check your network connection or try again later.')
        return

    content = base64.b64decode(content_encoded).decode('utf-8')
    name = path.split('/')[-1]

    DOWNLOADED_DIRECTORY_PATH.mkdir(exist_ok=True)
    with open(DOWNLOADED_DIRECTORY_PATH / name, 'w') as file:
        file.write(content)

    print(f'File "{path}" was downloaded.')


def check_download(owner_name, repo_name, branch, path) -> bool:
    try:
        repo = git.get_repo(f"{owner_name}/{repo_name}")
        commits = repo.get_commits(path=path, sha=branch)

        latest_commit = commits[0]
        name = path.split('/')[-1]
        file = DOWNLOADED_DIRECTORY_PATH / name

        if not file.exists():
            return True

        commit_date = latest_commit.commit.author.date
    except (UnknownObjectException, GithubException):
        print('Invalid data was passed.')
        return False
    except ConnectionError:
        print('No connection with Github. Please check your network connection or try again later.')
        return False

    creation_time = os.path.getctime(file)
    creation_date = datetime.fromtimestamp(creation_time, tz=timezone.utc)

    return commit_date > creation_date


def authenticate_token() -> None:
    print('Read about personal access token here and generate it to start use this application.\n'
          'Link: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic')
    token = input('Enter your secure token: ')

    try:
        global git
        git = Github(token)
        print('Authentication is successful.')
    except BadCredentialsException:
        print('You entered invalid secure token. Try again.\n')
        authenticate_token()
        return
    except ConnectionError:
        print('No connection with Github. Please check your network connection or try again later.')
        return

    AUTH_DIRECTORY_PATH.mkdir(exist_ok=True)
    with open(AUTH_FILE_PATH, 'w') as file:
        file.write(token)


def read_credentials() -> str:
    with open(AUTH_FILE_PATH, 'r') as file:
        return file.read()


def read_tracked_files() -> list:
    with open(FILES_FILE_PATH, 'r') as file:
        return [line.split() for line in file]


def show_tracked_files() -> None:
    try:
        files = read_tracked_files()

        if len(files) == 0:
            raise FileNotFoundError
        files.insert(0, ('Owner name', 'Repository name', 'Branch name', 'File path'))
    except FileNotFoundError:
        print('No files are currently being tracked.')
        return

    max_owner_len = max(len(line[0]) for line in files)
    max_repo_len = max(len(line[1]) for line in files)
    max_path_len = max(len(line[2]) for line in files)
    max_branch_len = max(len(line[3]) for line in files)

    [print(
        f'{line[0]:<{max_owner_len}} {line[1]:<{max_repo_len}} {line[2]:<{max_path_len}} {line[3]:<{max_branch_len}}')
        for line in files]


def update_all_tracked_files() -> None:
    try:
        files = read_tracked_files()

        if len(files) == 0:
            raise FileNotFoundError
    except FileNotFoundError:
        print('No files are currently being tracked.')
        return

    for file in files:
        if check_download(file[0], file[1], file[2], file[3]):
            download_file(file[0], file[1], file[2], file[3])
        else:
            print(f'File "{file[3]}" is up to date.')


def ask_user_for_data() -> tuple[str, str, str, str] | None:
    try:
        owner_name, repo_name, branch, path = parse_link()
    except ValueError:
        print('Wrong link format.')
        return

    try:
        try:
            git.get_user(owner_name)
        except UnknownObjectException:
            print(f'The user "{owner_name}" does not exist.')
            return

        try:
            repo = git.get_repo(f"{owner_name}/{repo_name}")
        except UnknownObjectException:
            print(f'The repository "{repo_name}" does not exist.')
            return

        try:
            repo.get_branch(branch)
        except GithubException:
            print(f'The branch "{branch}" does not exist in the repository "{repo_name}".')
            return

        try:
            repo.get_contents(path, ref=branch)
        except UnknownObjectException:
            print(f'The file "{path}" does not exist in the branch "{branch}".')
            return
    except ConnectionError:
        print('No connection with Github. Please check your network connection or try again later.')
        return

    return owner_name, repo_name, branch, path


def parse_link() -> tuple[str, str, str, str]:
    link_split = input('Enter a link to the file: ')
    pattern = r"https://github\.com/(?P<owner_name>[^/]+)/(?P<repo_name>[^/]+)/blob/(?P<branch>[^/]+)/(?P<path>.+)"
    match = re.match(pattern, link_split)

    if match:
        return (
            match.group('owner_name'),
            match.group('repo_name'),
            match.group('branch'),
            match.group('path')
        )
    else:
        raise ValueError


def delete_tracked_file() -> None:
    print('Deleting a file.')

    try:
        owner_name, repo_name, branch, path = parse_link()
    except ValueError:
        print('Wrong link format.')
        return

    line_to_delete = f'{owner_name} {repo_name} {branch} {path}'

    try:
        with open(FILES_FILE_PATH, 'r+') as file:
            lines = file.readlines()
            file.seek(0)

            if len(lines) == 0:
                raise FileNotFoundError

            for line in lines:
                if line.strip('\n') != line_to_delete:
                    file.write(line)
                else:
                    print(f'File "{path}" was deleted.')
                    break
            else:
                print(f'File "{path}" does not exist.')

            file.truncate()
    except FileNotFoundError:
        print('No files are currently being tracked.')


def update_tracked_file() -> None:
    print('Updating a file.')

    try:
        owner_name, repo_name, branch, path = parse_link()
    except ValueError:
        print('Wrong link format.')
        return

    download_file(owner_name, repo_name, branch, path)


def add_tracked_file() -> None:
    print('Adding a file.')

    try:
        owner_name, repo_name, branch, path = ask_user_for_data()
    except TypeError:
        return

    download_file(owner_name, repo_name, branch, path)

    FILES_DIRECTORY_PATH.mkdir(exist_ok=True)
    with open(FILES_FILE_PATH, 'a') as file:
        file.write(f'{owner_name} {repo_name} {branch} {path}\n')

    print(f'File "{path}" was successfully added to the list of tracked files.')


def download_file_without_tracking() -> None:
    try:
        owner_name, repo_name, branch, path = ask_user_for_data()
    except TypeError:
        return

    if check_download(owner_name, repo_name, branch, path):
        download_file(owner_name, repo_name, branch, path)
    else:
        print(f'File "{path}" is up to date.')


def delete_all_tracked_files() -> None:
    if FILES_FILE_PATH.exists():
        Path.unlink(FILES_FILE_PATH)
        print('All tracked files were deleted.')
    else:
        print('No files were being tracked.')


def start_thread() -> tuple[Event, Thread]:
    stop_event = threading.Event()
    thread = threading.Thread(target=auto_update_files, args=(stop_event,))
    thread.start()
    return stop_event, thread


def auto_update_files(stop_event) -> None:
    while not stop_event.is_set():
        for file in read_tracked_files():
            if check_download(file[0], file[1], file[2], file[3]):
                download_file(file[0], file[1], file[2], file[3])
                # print(f'"{file[3]}" was updated')
            # else:
            #     print(f'"{file[3]}" was not updated')
        stop_event.wait(15)


def manual() -> None:
    print(textwrap.dedent('''
    Q: How to generate an access token?
    A: Link: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic
    
    Q: Where can I report about bugs and send any idea regarding this project?
    A: Link: https://github.com/revel111/GithubDownloader/issues 
    I ask you to report any kind of bugs. Each bug will be fixed and any idea will be reviewed.
    '''))


def main_menu() -> None:
    while True:
        print('===============================================\n'
              'You are logged in as ' + git.get_user().login)
        print(textwrap.dedent('''
            Type 1 if you want to change credentials.
            Type 2 to show all tracked files.
            Type 3 to add a new tracked file and download it.
            Type 4 to immediately update all tracked files.
            Type 5 to update a specific tracked file. #TODO
            Type 6 to download a file.
            Type 7 to delete a tracked file. #TODO
            Type 8 to delete all tracked files.
            Type 10 to see the manual (help).
            Type 0 to exit.
        '''))
        ch = input('Type: ')
        print('===============================================')

        match ch:
            case '1':
                authenticate_token()
            case '2':
                show_tracked_files()
            case '3':
                add_tracked_file()
            case '4':
                update_all_tracked_files()
            case '5':
                update_tracked_file()
            case '6':
                download_file_without_tracking()
            case '7':
                delete_tracked_file()
            case '8':
                delete_all_tracked_files()
            case '10':
                manual()
            case '0':
                raise KeyboardInterrupt
            case _:
                print('Wrong input.')


def main() -> None:
    print('Github downloader v1.0 by revel111.')

    if not AUTH_FILE_PATH.exists():
        authenticate_token()
    else:
        try:
            global git
            git = Github(read_credentials())
        except BadCredentialsException:
            authenticate_token()

    stop_event, thread = start_thread()
    try:
        main_menu()
    except KeyboardInterrupt:
        stop_event.set()
        thread.join()
        print('Thank you for using this application.')


if __name__ == '__main__':
    main()
