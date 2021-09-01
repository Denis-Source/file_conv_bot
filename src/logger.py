import logging
import os

from config import Config


class Logger(logging.Logger, Config):
    LOGGER_FORMAT = "%(asctime)s\t%(levelname)-7s\t%(name)-8s\t%(message)s"

    def __init__(self, name):
        super().__init__(name)
        self.add_f_handler()
        self.add_c_handler()

    def add_f_handler(self):
        """
        File handler
        Creates a folder if it doesn't exist
        Sets a level and a formatter
        :return: None
        """
        if not os.path.exists(self.LOGGING_FOLDER):
            os.makedirs(self.LOGGING_FOLDER)
        handler = logging.FileHandler(self.LOGGING_PATH)
        handler.setLevel(self.LOGGING_FILE_LEVEL)
        formatter = logging.Formatter(self.LOGGER_FORMAT)
        handler.setFormatter(formatter)
        self.addHandler(handler)

    def add_c_handler(self):
        """
        Command line handler
        Creates a folder if it doesn't exist
        Sets a level and a formatter
        :return: None
        """
        handler = logging.StreamHandler()
        handler.setLevel(self.LOGGING_COMMAND_LINE_LEVEL)
        formatter = logging.Formatter(self.LOGGER_FORMAT)
        handler.setFormatter(formatter)
        self.addHandler(handler)
