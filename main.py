import textwrap
from pathlib import Path

from github import Github, BadCredentialsException
from requests.exceptions import ConnectionError
from tabulate import tabulate

import global_variables as gv
from funcs import read_tracked_files, validate_path, return_manual, parse_link, read_credentials, \
    delete_all_tracked_files, download_file, delete_tracked_file, authenticate_token, check_download, validate_data, \
    save_tracked_file
from global_variables import DOWNLOADED_DIRECTORY_PATH, AUTH_FILE_PATH, GeneralException


def console_and_return_tracked_files() -> list | None:
    try:
        files = read_tracked_files()
    except FileNotFoundError:
        print('No files are currently being tracked.')
        return None

    if not files:
        print('No files are currently being tracked.')
        return None

    print(tabulate(files, headers=['№', 'Owner name', 'Repository name', 'Branch name', 'File path', 'Stored'],
                   showindex="always"))

    return files


def update_all_tracked_files() -> None:
    try:
        files = read_tracked_files()
    except FileNotFoundError:
        print('No files are currently being tracked.')
        return

    if not files:
        print('No files are currently being tracked.')
        return

    for file in files:
        if check_download(file[0], file[1], file[2], file[3], file[4]):
            console_download_file(file[0], file[1], file[2], file[3], file[4])
        else:
            print(f'File "{file[3]}" is up to date.')


def ask_user_for_data() -> tuple[str, str, str, str, Path] | None:
    try:
        link = input('Enter a link to the file: ')
        owner_name, repo_name, branch, path = parse_link(link)
    except ValueError:
        print('Wrong link format.')
        return

    try:
        validate_data(owner_name, repo_name, branch, path)
    except GeneralException as e:
        print(e)
        return

    input_loc = input('Enter a path where you want to store a file: ')
    location = validate_path(Path(input_loc))

    if location == DOWNLOADED_DIRECTORY_PATH:
        print(
            f'Location "{input_loc}" does not exist. File will be stored in the "{DOWNLOADED_DIRECTORY_PATH}"')

    return owner_name, repo_name, branch, path, location


def delete_tracked_file_by_index() -> None:
    files = console_and_return_tracked_files()

    if not files:
        return
    try:
        ch = int(input('Type index of file you want to update: '))
        print(delete_tracked_file(f'{files[ch][0]}{files[ch][1]}{files[ch][2]}{files[ch][3]}', files[ch][3]))
    except GeneralException as e:
        print(e)
    except (IndexError, ValueError):
        print('Wrong input.')


def update_tracked_file() -> None:
    files = console_and_return_tracked_files()

    if not files:
        return

    try:
        ch = int(input('Type index of file you want to update: '))
        if check_download(files[ch][0], files[ch][1], files[ch][2], files[ch][3], files[ch][4]):
            console_download_file(files[ch][0], files[ch][1], files[ch][2], files[ch][3], files[ch][4])
        else:
            print(f'File "{files[ch][3]}" is up to date.')
    except (IndexError, ValueError):
        print('Wrong input.')


def add_tracked_file() -> None:
    print('Adding a file.')

    try:
        owner_name, repo_name, branch, path, location = ask_user_for_data()
    except TypeError:
        return

    console_download_file(owner_name, repo_name, branch, path, location)

    save_tracked_file(owner_name, repo_name, branch, path, location)

    print(f'File "{path}" was successfully added to the list of tracked files.')


def console_download_file_without_tracking() -> None:
    try:
        owner_name, repo_name, branch, path, location = ask_user_for_data()
    except TypeError:
        return

    console_download_file(owner_name, repo_name, branch, path, location)


def console_download_file(owner_name: str, repo_name: str, branch: str, path: str, location: str) -> None:
    try:
        download_file(owner_name, repo_name, branch, path, location)
    except GeneralException as e:
        print(e)


def console_delete_all_tracked_files() -> None:
    try:
        delete_all_tracked_files()
    except GeneralException as e:
        print(e)


def console_delete_tracked_file_by_link() -> None:
    try:
        delete_tracked_file_by_link(input('Enter a link to the file: '))
    except GeneralException as e:
        print(e)


def delete_tracked_file_by_link(link: str) -> None:
    try:
        owner_name, repo_name, branch, path = parse_link(link)
    except ValueError:
        raise gv.WarningException('Wrong input.')

    try:
        delete_tracked_file(f'{owner_name}{repo_name}{branch}{path}', path.split('/')[-1])
    except GeneralException as e:
        print(e)


def manual() -> None:
    print(return_manual())


def main_menu() -> None:
    while True:
        print('=================================================')
        try:
            print(f'You are logged in as {gv.git.get_user().login}')
        except BadCredentialsException:
            print('You are logged in as anonymous. Enter a valid access token.')

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
                console_authenticate_token()
            case '2':
                console_and_return_tracked_files()
            case '3':
                add_tracked_file()
            case '4':
                update_all_tracked_files()
            case '5':
                update_tracked_file()
            case '6':
                console_download_file_without_tracking()
            case '7':
                delete_tracked_file_by_index()
            case '8':
                console_delete_tracked_file_by_link()
            case '9':
                console_delete_all_tracked_files()
            case '10':
                manual()
            case '0':
                raise KeyboardInterrupt
            case _:
                print('Wrong input.')


def console_authenticate_token() -> None:
    print('Read about personal access token here and generate it to start use this application.\n'
          'Link: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic')
    token = input('Enter your secure token: ')

    try:
        authenticate_token(token)
    except GeneralException as e:
        print(e)
        return


def main() -> None:
    print('Github downloader v1.0 by revel111.')

    if not AUTH_FILE_PATH.exists():
        print('No access token was provided.')
    else:
        try:
            gv.git = Github(read_credentials())
            gv.git.get_user().login
        except BadCredentialsException:
            print('Invalid access token was provided.')

    try:
        main_menu()
    except ConnectionError:
        print('No connection with Github. Please check your network connection or try again later.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Thank you for using this application.')
