import time
from datetime import datetime

from github import Github, BadCredentialsException

from funcs import read_tracked_files, read_credentials
from global_variables import AUTH_FILE_PATH, LOG_PATH, GeneralException
from main import download_file, check_download

git = Github()


def run() -> None:
    while True:
        try:
            auto_update_files()
            log('Files were updated.')
        except ConnectionError:
            log('No connection with Github.')
        time.sleep(900)  # 15 minutes
        # time.sleep(15)


def check_run() -> bool:
    if not AUTH_FILE_PATH.exists():
        return False

    try:
        global git
        git = Github(read_credentials())
        git.get_user().login
    except BadCredentialsException:
        log('Invalid token was passed.')
        return False
    except ConnectionError:
        log('No connection with Github.')
        return False

    return True


def auto_update_files() -> None:
    try:
        files = read_tracked_files()
    except FileNotFoundError:
        return

    for file in files:
        if check_download(file[0], file[1], file[2], file[3], file[4]):
            try:
                download_file(file[0], file[1], file[2], file[3], file[4])
            except GeneralException:
                pass


def log(message) -> None:
    with open(LOG_PATH, 'a') as file:
        file.write(f'{datetime.now()} {message}' + '\n')


if __name__ == '__main__':
    try:
        if check_run():
            log(f'Logged in as: {git.get_user().login}')
            run()
        else:
            log(f'Unable to login.')
    except KeyboardInterrupt:
        pass
