import cv2
import shutil

from src.converters.converter import *
from src.logger import Logger


class VideoConverter(Converter):
    """
    Video Converter class used for converting videos in defined formats
    Depends on cv2 library

    """

    AVAILABLE_FORMATS = ["frame"]

    def __init__(self):
        super().__init__()
        self.logger = Logger("vid_conv")

    def frame_video(self, video_path):
        """
        Splits video in frames and returns a filepath of an zip archive
        In process creates temporary folder with every frame (deletes it when finishes)
        Requires lots of both time and space

        :param video_path: str
        :return: str
        """
        self.logger.debug(f"Framing video at {video_path}")

        video = cv2.VideoCapture(video_path)
        count = 0
        temp_folder = self.generate_temp_folder()
        success, image = video.read()
        while success:
            file_path = os.path.join(temp_folder, f"{count}.jpeg")
            cv2.imwrite(file_path, image)
            success, image = video.read()
            count += 1

        arc_path = self.generate_temp_path()
        arc_format = "zip"

        self.logger.debug(f"Archiving frames at {arc_path}.{arc_format}")
        shutil.make_archive(arc_path, arc_format, temp_folder)

        self.logger.debug(f"Deleting folder at {temp_folder}")
        shutil.rmtree(temp_folder)

        self.logger.info(f"Video at {video_path} framed total of: {count} frames")
        return f"{arc_path}.{arc_format}"
