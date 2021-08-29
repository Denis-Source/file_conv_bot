import time
import os

from src.logger import Logger
from config import Config


class ImageConversionException(Exception):
    pass


class SameFormatConversionException(ImageConversionException):
    pass


class UnsupportedFormatException(ImageConversionException):
    pass


class Converter(Config):
    """
    Base Converter class
    """
    def __init__(self):
        self.logger = Logger("conv")
        self.temp_folder = os.path.join(self.BASE_DIR, self.TEMP_FOLDER)
        if not os.path.exists(self.temp_folder):
            os.makedirs(self.temp_folder)
            self.logger.info(f"Created temp folder at {self.temp_folder}")

    def generate_temp_path(self, file_format=""):
        """
        Creates a temporary filename and returns it's full path
        if no file_format returns bare filename (no format)
        :param file_format: str
        :return: str
        """
        file_name = os.path.join(
            self.temp_folder,
            f"temp_{str(time.time()).replace('.', '')}"
        )
        if file_format:
            file_name += f".{file_format}"
        self.logger.debug(f"Created filename at {file_name}")
        return file_name

    def generate_temp_folder(self):
        """
        Creates and returns full folder path
        :return: str
        """
        folder_name = str(time.time()).replace(".", "")
        folder_path = os.path.join(self.temp_folder, folder_name)
        os.makedirs(folder_path)
        self.logger.debug(f"Created nested temp folder at {folder_path}")
        return folder_path

    def delete_file(self, file_path):
        """
        Deletes a file
        :param file_path: str
        :return: None
        """
        try:
            os.remove(file_path)
            self.logger.debug(f"Deleted file at {file_path}")
        except PermissionError:
            self.logger.error(f"Error deleting file {file_path}")

    def find_file_by_id(self, file_id):
        temp_folder = self.TEMP_FOLDER
        files = os.listdir(temp_folder)
        for file in files:
            if str(file_id) in file:
                filepath = os.path.join(temp_folder, file)
                self.logger.debug(f"File with id {file_id} found at {filepath}")
                return filepath
