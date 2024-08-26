import time

from github import Github, BadCredentialsException

from main import AUTH_FILE_PATH, read_credentials, auto_update_files, log

git = Github()


def run() -> None:
    while True:
        auto_update_files()
        log('Updating files')
        time.sleep(15)


def check_run() -> bool:
    if not AUTH_FILE_PATH.exists():
        return False

    try:
        global git
        git = Github(read_credentials())
        print(git.get_user().login)
    except BadCredentialsException:
        return False

    return True


if __name__ == '__main__':
    try:
        if check_run():
            log(f'Logged in as: {git.get_user().login}')
            run()
        else:
            log(f'Unable to login.')
    except ConnectionError:
        log('No connection with Github. Please check your network connection or try again later.')
    except KeyboardInterrupt:
        pass
