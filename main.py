import base64
import os.path
from datetime import datetime
from pathlib import Path
import textwrap

from github import Github, BadCredentialsException, UnknownObjectException, GithubException
from requests.exceptions import ConnectionError

CURRENT_FILE_PATH = Path(__file__).parent.resolve()
AUTH_DIRECTORY_PATH = CURRENT_FILE_PATH / 'auth'
AUTH_FILE_PATH = AUTH_DIRECTORY_PATH / 'credentials.txt'
FILES_DIRECTORY_PATH = CURRENT_FILE_PATH / 'data'
FILES_FILE_PATH = FILES_DIRECTORY_PATH / 'files.txt'
DOWNLOADED_DIRECTORY_PATH = CURRENT_FILE_PATH / 'downloaded'
git = Github()


def get_last_commit_date(repo_url, file_path) -> datetime:
    owner, repo_name = repo_url.split('/')[-2:]

    repo = git.get_repo(owner + '/' + repo_name)
    commits = repo.get_commits(path=file_path)

    return commits[0].commit.committer.date


def download_file(owner_name, repo_name, branch, path) -> None:
    try:
        repo = git.get_repo(owner_name + '/' + repo_name)
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

    print(f'File "{path}" was downloaded and updated.')


def check_download(file_path) -> None:
    commit_date = get_last_commit_date('https://github.com/a2x/cs2-dumper', 'output/offsets.cs')
    date_updated = None

    if os.path.exists(file_path):
        date_updated = datetime.fromtimestamp(os.path.getmtime(file_path))

    if date_updated is None or date_updated < commit_date:
        download_file()


def authenticate_token() -> None:
    print('''Read about personal access token here and generate it to start use this application.
Link: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic''')
    token = input('Enter your secure token: ')

    try:
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

    for line in files:
        print(
            f'{line[0]:<{max_owner_len}} {line[1]:<{max_repo_len}} {line[2]:<{max_path_len}} {line[3]:<{max_branch_len}}')


def update_all_tracked_files() -> None:
    try:
        files = read_tracked_files()
        if len(files) == 0:
            raise FileNotFoundError
    except FileNotFoundError:
        print('No files are currently being tracked.')
        return

    for file in files:
        download_file(file[0], file[1], file[2], file[3])


def ask_user_for_data() -> tuple[str, str, str, str] | None:
    owner_name = input('Enter a name of owner: ')

    try:
        try:
            git.get_user(owner_name)
        except UnknownObjectException:
            print(f'The user "{owner_name}" does not exist.')
            add_tracked_file()
            return

        repo_name = input('Enter a name of repository: ')

        try:
            repo = git.get_repo(owner_name + '/' + repo_name)
        except UnknownObjectException:
            print(f'The repository "{repo_name}" does not exist.')
            add_tracked_file()
            return

        branch = input('Enter a branch of the project: ')

        try:
            repo.get_branch(branch)
        except GithubException:
            print(f'The branch "{branch}" does not exist in the repository.')
            add_tracked_file()
            return

        path = input('Enter a path to the file: ')

        try:
            repo.get_contents(path, ref=branch)
        except UnknownObjectException:
            print(f'The file "{path}" does not exist in the branch "{branch}".')
            add_tracked_file()
            return
    except ConnectionError:
        print('No connection with Github. Please check your network connection or try again later.')
        return

    return owner_name, repo_name, branch, path


def ask_user_for_raw_data() -> tuple[str, str, str, str]:
    return (input('Enter a name of owner: '),
            input('Enter a name of repository: '),
            input('Enter a branch of the project: '),
            input('Enter a path to the file: '))


def delete_tracked_file() -> None:
    print('Deleting a file.')
    owner_name, repo_name, branch, path = ask_user_for_raw_data()
    # owner_name = 'a2x'
    # repo_name = 'cs2-dumper'
    # branch = 'main'
    # path = '/src/main.rs'
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
                    print(f'File {path} was deleted.')
                    break
            else:
                print(f'File {path} does not exist.')

            file.truncate()
    except FileNotFoundError:
        print('No files are currently being tracked.')


def update_tracked_file() -> None:
    print('Updating a file.')
    owner_name, repo_name, branch, path = ask_user_for_raw_data()
    download_file(owner_name, repo_name, branch, path)


def add_tracked_file() -> None:
    print('Adding a file.')
    owner_name, repo_name, branch, path = ask_user_for_data()

    FILES_DIRECTORY_PATH.mkdir(exist_ok=True)
    with open(FILES_FILE_PATH, 'a') as file:
        file.write(f'{owner_name} {repo_name} {branch} {path}\n')

    print(f'File "{path}" was successfully added to the list of tracked files.')


def delete_all_tracked_files() -> None:
    if FILES_FILE_PATH.exists():
        Path.unlink(FILES_FILE_PATH)
        print('All tracked files were deleted.')
    else:
        print('No files were being tracked.')


def start_thread() -> None:
    pass


def manual():
    print('''
    Q: How to generate an access token?
    A: Link: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic
    
    Q: How to exit to the main menu(e.g. when being in the menu with adding a new file)?
    A: Press 'Esc'.
    
    Q: Where can I report about bugs and send any idea regarding this project?
    A: Link: https://github.com/revel111/GithubDownloader/issues 
    I ask you to report any kind of bugs. Each bug will be fixed and any idea will be reviewed.
    ''')


def main_menu() -> None:
    print('Github downloader v1.0 by revel111.')
    if not AUTH_FILE_PATH.exists():
        authenticate_token()
    else:
        try:
            git = Github(read_credentials())
        except BadCredentialsException:
            authenticate_token()

    while True:
        print('===============================================\n'
              'You are logged in as ' + git.get_user().login)
        ch = input(textwrap.dedent('''
            Type 1 if you want to change credentials.
            Type 2 to show all tracked files.
            Type 3 to add a new tracked file.
            Type 4 to immediately update all tracked files.
            Type 5 to update a specific tracked file.
            Type 6 to delete a tracked file.
            Type 7 to delete all tracked files.
            Type 10 to see the manual (help).
            Type 0 to exit.
        '''))
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
                delete_tracked_file()
            case '7':
                delete_all_tracked_files()
            case '10':
                manual()
            case '0':
                break
            case _:
                print('Wrong input.')
    print('Thank you for using this application.')


if __name__ == '__main__':
    # commit_date = get_last_commit_date('https://github.com/a2x/cs2-dumper', 'output/offsets.cs')
    main_menu()
    # delete_tracked_file()
    # git = Github(read_credentials())
    # download_file('a2x', 'cs2-dumper', 'main', '/src/main.rs')
    # update_all_tracked_files()
    # owner_name = 'a2x'
    # repo_name = 'cs2-dumper'
    # branch = 'main'
    # path = '/src/main.rs'
