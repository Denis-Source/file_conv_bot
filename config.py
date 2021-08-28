from logging import DEBUG, INFO, WARNING, ERROR
from os.path import abspath, join
from os import getcwd


class Config:
    BOT_TOKEN = "bot_token"
    SERVER_PORT = 5000

    BASE_DIR = abspath(getcwd())

    TEMP_FOLDER = "temp"

    LOGGING_FOLDER = join(BASE_DIR, "log")
    LOGGING_PATH = join(LOGGING_FOLDER, "log.log")
    LOGGING_FILE_LEVEL = DEBUG
    LOGGING_COMMAND_LINE_LEVEL = ERROR
