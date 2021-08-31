from PIL import Image
from PIL import UnidentifiedImageError

from src.converters.converter import *
from src.logger import Logger


class ImageConverter(Converter):
    """
    Image Converter class used for converting images in defined formats (AVAILABLE_FORMATS)
    """
    AVAILABLE_FORMATS = ["ico", "bmp", "jpeg", "png", "jpg", "webp"]

    def __init__(self):
        super().__init__()
        self.logger = Logger("img_conv")

    def convert(self, image_path, new_format):
        """
        Converts an image from image path to a specified format
        Creates temporary file in doing so
        Returns byte array
        :param image_path: str
        :param new_format: str
        :return: bytes
        :raises: UnsupportedFormatException
        :raises: SameFormatConversionException
        """
        self.logger.debug(f"Converting image to {new_format}")

        if new_format not in self.AVAILABLE_FORMATS:
            self.logger.error(f"Format {new_format} is the same")
            raise UnsupportedFormatException
        try:
            with Image.open(image_path) as image:
                if image.format == new_format:
                    self.logger.error(f"Format {new_format} is the same")
                    raise UnsupportedFormatException

                image.convert("RGB")
                new_image_path = self.generate_temp_path(new_format)
                image.save(new_image_path, format=new_format)
                image.close()
                self.logger.info(f"Converted image from {image.format} to {new_format}")
                return new_image_path

        except UnidentifiedImageError:
            raise UnsupportedFormatException
