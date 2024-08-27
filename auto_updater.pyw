import time

from github import Github, BadCredentialsException

from main import AUTH_FILE_PATH, read_credentials, auto_update_files, log

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


if __name__ == '__main__':
    try:
        if check_run():
            log(f'Logged in as: {git.get_user().login}')
            run()
        else:
            log(f'Unable to login.')
    except KeyboardInterrupt:
        pass
