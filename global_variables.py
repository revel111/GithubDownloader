from pathlib import Path

from github import Github

CURRENT_FILE_PATH = Path(__file__).parent.resolve()
FILES_DIRECTORY_PATH = CURRENT_FILE_PATH / 'data'
AUTH_FILE_PATH = FILES_DIRECTORY_PATH / 'credentials.env'
FILES_FILE_PATH = FILES_DIRECTORY_PATH / 'files.txt'
DOWNLOADED_DIRECTORY_PATH = CURRENT_FILE_PATH / 'downloaded'
LOG_PATH = CURRENT_FILE_PATH / 'log.txt'

git = Github()


class GeneralException(Exception):
    pass


class SuccessException(GeneralException):
    pass


class ErrorException(GeneralException):
    pass


class WarningException(GeneralException):
    pass


class InfoException(GeneralException):
    pass
