from logging import DEBUG, INFO, WARNING, ERROR
from os.path import abspath, join
from os import getcwd


class Config:
    BOT_TOKEN = "1595761097:AAHsNE3ysMUJIutK5anLJ-pUll7oZug8uog"
    SERVER_PORT = 5000

    BASE_DIR = abspath(getcwd())

    TEMP_FOLDER = "temp"

    LOGGING_FOLDER = join(BASE_DIR, "log")
    LOGGING_PATH = join(LOGGING_FOLDER, "log.log")
    LOGGING_FILE_LEVEL = DEBUG
    LOGGING_COMMAND_LINE_LEVEL = ERROR

    ADMIN_TELEGRAM_ID = 395450682
