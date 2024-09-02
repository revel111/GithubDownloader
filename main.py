import base64
import os.path
import re
import textwrap
from datetime import datetime, timezone
from pathlib import Path

from github import Github, BadCredentialsException, UnknownObjectException, GithubException
from requests.exceptions import ConnectionError
from tabulate import tabulate

CURRENT_FILE_PATH = Path(__file__).parent.resolve()
FILES_DIRECTORY_PATH = CURRENT_FILE_PATH / 'data'
AUTH_FILE_PATH = FILES_DIRECTORY_PATH / 'credentials.txt'
FILES_FILE_PATH = FILES_DIRECTORY_PATH / 'files.txt'
DOWNLOADED_DIRECTORY_PATH = CURRENT_FILE_PATH / 'downloaded'
LOG_PATH = CURRENT_FILE_PATH / 'log.txt'
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


def log(message) -> None:
    with open(LOG_PATH, 'a') as file:
        file.write(f'{datetime.now()} {message}' + '\n')


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
        git.get_user().login
        print('Authentication is successful.')
    except BadCredentialsException:
        print('You entered invalid secure token. Try again.\n')
        authenticate_token()
        return
    except ConnectionError:
        print('No connection with Github. Please check your network connection or try again later.')
        return

    FILES_DIRECTORY_PATH.mkdir(exist_ok=True)
    with open(AUTH_FILE_PATH, 'w') as file:
        file.write(token)


def read_credentials() -> str:
    with open(AUTH_FILE_PATH, 'r') as file:
        return file.read()


def read_tracked_files() -> list:
    with open(FILES_FILE_PATH, 'r') as file:
        files = [line.split() for line in file]

    if not files:
        raise FileNotFoundError

    return files


def show_and_return_tracked_files() -> list | None:
    try:
        files = read_tracked_files()
    except FileNotFoundError:
        print('No files are currently being tracked.')
        return None

    print(tabulate(files,
                   headers=['№', 'Owner name', 'Repository name', 'Branch name', 'File path'], showindex="always"))

    return files


def update_all_tracked_files() -> None:
    try:
        files = read_tracked_files()
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
    link = input('Enter a link to the file: ')
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


def delete_tracked_file_by_index() -> None:
    files = show_and_return_tracked_files()

    if not files:
        return
    try:
        ch = int(input('Type index of file you want to update: '))
        delete_tracked_file(f'{files[ch][0]} {files[ch][1]} {files[ch][2]} {files[ch][3]}', files[ch][3])
    except (IndexError, ValueError):
        print('Wrong input.')
        return


def delete_tracked_file_by_link() -> None:
    try:
        owner_name, repo_name, branch, path = parse_link()
    except ValueError:
        print('Wrong input.')
        return

    delete_tracked_file(f'{owner_name} {repo_name} {branch} {path}', path.split('/')[-1])


def delete_tracked_file(line_to_delete, name) -> None:
    try:
        with open(FILES_FILE_PATH, 'r+') as file:
            flag = False
            lines = file.readlines()
            file.seek(0)

            if len(lines) == 0:
                raise FileNotFoundError

            for line in lines:
                if line.strip('\n') != line_to_delete:
                    file.write(line)
                else:
                    flag = True

            if flag:
                print(f'File "{name}" was deleted.')
            else:
                print(f'File "{name}" does not exist.')

            file.truncate()
    except FileNotFoundError:
        print('No files are currently being tracked.')


def update_tracked_file() -> None:
    files = show_and_return_tracked_files()

    if not files:
        return

    try:
        ch = int(input('Type index of file you want to update: '))
        if check_download(files[ch][0], files[ch][1], files[ch][2], files[ch][3]):
            download_file(files[ch][0], files[ch][1], files[ch][2], files[ch][3])
        else:
            print(f'File "{files[ch][3]}" is up to date.')
    except (IndexError, ValueError):
        print('Wrong input.')


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


def auto_update_files() -> None:
    try:
        files = read_tracked_files()
    except FileNotFoundError:
        return

    for file in files:
        if check_download(file[0], file[1], file[2], file[3]):
            download_file(file[0], file[1], file[2], file[3])
            print(f'"{file[3]}" was updated')
        else:
            print(f'"{file[3]}" was not updated')


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
        print('=================================================\n'
              'You are logged in as ' + git.get_user().login)
        print(textwrap.dedent('''
            Type 1 if you want to change credentials.
            Type 2 to show all tracked files.
            Type 3 to add a new tracked file and download it.
            Type 4 to immediately update all tracked files.
            Type 5 to update a specific tracked file.
            Type 6 to download a file.
            Type 7 to delete a tracked file.
            Type 8 to delete a tracked file by link.
            Type 9 to delete all tracked files.
            Type 10 to see the manual (help).
            Type 0 to exit.
        '''))
        ch = input('Type: ')
        print('=================================================')

        match ch:
            case '1':
                authenticate_token()
            case '2':
                show_and_return_tracked_files()
            case '3':
                add_tracked_file()
            case '4':
                update_all_tracked_files()
            case '5':
                update_tracked_file()
            case '6':
                download_file_without_tracking()
            case '7':
                delete_tracked_file_by_index()
            case '8':
                delete_tracked_file_by_link()
            case '9':
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
            git.get_user().login
        except BadCredentialsException:
            authenticate_token()

    try:
        main_menu()
    except ConnectionError:
        print('No connection with Github. Please check your network connection or try again later.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Thank you for using this application.')
