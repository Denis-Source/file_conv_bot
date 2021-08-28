import json
import os
import requests

from src.logger import Logger
from config import Config
from src.converters import image_converter, video_coverter, document_converter
from src.converters.converter import UnsupportedFormatException
from src.bot.bot_file_history import BotFileHistory


class Bot(Config):
    """
    Bot class used for document, image, video conversion
    """
    TELEGRAM_API = "https://api.telegram.org"

    def __init__(self, lang="eng"):
        self.phrases_file = "phrases.json"
        self.lang = lang

        self.image_converter = image_converter.ImageConverter()
        self.video_converter = video_coverter.VideoConverter()
        self.document_converter = document_converter.DocumentConverter()

        self.logger = Logger("bot")
        self.file_history = BotFileHistory()

    @property
    def text_data(self):
        """
        Open json document with phrases used for messages
        Has different languages
        :return: dict
        """
        base_dir = os.path.abspath(os.getcwd())
        file_path = os.path.join(base_dir, self.phrases_file)
        with open(file_path, "r", encoding="utf-8") as f:
            self.logger.info(f"{self.phrases_file} is read")
            return json.load(f)

    def get_answer(self, action):
        """
        Gets answer from text_data property
        :param action: str
        :return: str
        """
        return self.text_data[action][self.lang]

    def get_url(self, method):
        """
        Generates url to telegram api with supplied method
        :param method: str
        :return: str
        """
        return f"{self.TELEGRAM_API}" \
               f"/bot" \
               f"{self.BOT_TOKEN}" \
               f"/{method}"

    def send_message(self, context, message, is_phrase=True):
        """
        Sends message to user
        Can use phrases from get_answer message
        :param context: dict
        :param message: str
        :param is_phrase: bool
        :return: None
        """
        if is_phrase:
            message = self.get_answer(message)
        data = {"chat_id": context["from"]["id"],
                "text": message}
        requests.post(url=self.get_url("sendMessage"), data=data)
        if not is_phrase:
            message = "other"
        self.logger.info(f"Message {message} sent to {context['from']['id']}")

    def send_document(self, context, file_path):
        """
        Sends document to telegram to user
        :param context: dict
        :param file_path: str
        :return: None
        """
        with open(file_path, "rb") as document:
            data = {"chat_id": context["from"]["id"]}
            file = {"document": document}
            requests.post(url=self.get_url(method="sendDocument"), data=data, files=file)
            self.logger.info(f"Document {file_path} sent to {context['from']['id']}")

    def download_document(self, file_id):
        """
        Downloads file from telegram api and stores it as a temporary file
        Returns filepath
        Firstly requests telegram api to find url to file
        Secondly downloads it to a temporary folder
        :param file_id: str
        :return: str
        """
        self.logger.debug(f"Finding file with id {file_id}")
        response = requests.get(
            f"{self.TELEGRAM_API}"
            f"/bot"
            f"{self.BOT_TOKEN}"
            f"/getFile?file_id="
            f"{file_id}"
        )

        url_filepath = response.json()["result"]["file_path"]

        self.logger.debug(f"Downloading file {file_id} in memory")
        response = requests.get(f"{self.TELEGRAM_API}"
                                f"/file"
                                f"/bot"
                                f"{self.BOT_TOKEN}"
                                f"/{url_filepath}",
                                stream=True)
        file_format = url_filepath.split(".")[-1]

        temp_filepath = os.path.join(self.document_converter.TEMP_FOLDER, f"{file_id}.{file_format}")
        self.logger.debug(f"Saving file at {temp_filepath}")
        with open(temp_filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        self.logger.debug(f"File saved at {temp_filepath}")
        return temp_filepath

    def process_image(self, context):
        """
        Sends message about image formats
        :param context: dict
        :return: None
        """
        self.logger.debug("Document with supported image format detected")
        self.send_message(context, "image_detected")
        self.send_message(context,
                          ", ".join(self.image_converter.AVAILABLE_FORMATS), is_phrase=False)

    def process_document(self, context):
        """
        Sends message about document formats
        :param context: dict
        :return: None
        """
        self.logger.debug("Document with supported document format detected")
        self.send_message(context, "document_detected")
        self.send_message(context,
                          ", ".join(self.document_converter.AVAILABLE_OUTPUT_FORMATS), is_phrase=False)

    def process_video(self, context):
        """
        Sends message about video formats
        :param context: dict
        :return: None
        """
        self.logger.debug("Document with supported video format detected")
        self.send_message(context, "video_detected")
        self.send_message(context,
                          ", ".join(self.video_converter.AVAILABLE_FORMATS), is_phrase=False)

    def process_media(self, context):
        """
        Processes media if document is received
        :param context: dict
        :return: None
        """
        if "document" in context:
            self.logger.debug("Document detected")

            file_id = context["document"]["file_id"]
            self.file_history[context["from"]["id"]] = file_id

            document_path = self.download_document(file_id)
            file_format = document_path.split(".")[-1]

            if file_format in self.image_converter.AVAILABLE_FORMATS:
                self.process_image(context)

            elif file_format in self.document_converter.AVAILABLE_INPUT_FORMATS:
                self.process_document(context)

            elif file_format in self.video_converter.AVAILABLE_FORMATS:
                self.process_video(context)

            else:
                self.logger.debug(f"Document format {file_format} not supported")
                self.send_message(context, "not_supported_format")

    def process_command(self, context):
        """
        Sends command reply if command received
        :param context: dict
        :return: None
        """
        if context["text"] == "/start":
            self.send_message(context, "start")
        elif context["text"] == "/formats":
            self.send_message(context, "available_formats")
            self.send_message(context, "available_formats_images")
            self.send_message(context, ", ".join(self.image_converter.AVAILABLE_FORMATS), is_phrase=False)
            self.send_message(context, "available_formats_documents")
            self.send_message(context, ", ".join(self.document_converter.AVAILABLE_INPUT_FORMATS), is_phrase=False)
            self.send_message(context, "available_formats_video")
            self.send_message(context, ", ".join(self.video_converter.AVAILABLE_FORMATS), is_phrase=False)

    def convert_image(self, context, file_id):
        """
        Converts and sends received image
        :param context: dict
        :param file_id: str
        :return: None
        """
        file_path = self.image_converter.find_file_by_id(file_id)
        old_format = file_path.split(".")[-1]
        if old_format in self.image_converter.AVAILABLE_FORMATS:
            new_file_path = self.image_converter.convert(file_path, context["text"])
            self.send_document(context, new_file_path)
            self.logger.debug("Image conversion successful")
            self.image_converter.delete_file(new_file_path)

    def convert_document(self, context, file_id):
        """
        Converts and sends received document
        :param context: dict
        :param file_id: str
        :return: None
        """
        file_path = self.document_converter.find_file_by_id(file_id)
        old_format = file_path.split(".")[-1]
        if old_format in self.document_converter.AVAILABLE_INPUT_FORMATS:
            new_file_path = self.document_converter.convert(file_path, context["text"])
            self.send_document(context, new_file_path)
            self.logger.debug("Document conversion successful")
            self.document_converter.delete_file(new_file_path)

    def convert_video(self, context, file_id):
        """
        Converts and sends received video
        :param context: dict
        :param file_id: str
        :return: None
        """
        file_path = self.video_converter.find_file_by_id(file_id)
        old_format = file_path.split(".")[-1]
        if old_format in self.video_converter.AVAILABLE_FORMATS:  # TODO
            if context["text"] == "frame":
                new_file_path = self.video_converter.frame_video(file_path)
                self.send_document(context, new_file_path)
                self.logger.debug("Video conversion successful")
                self.video_converter.delete_file(new_file_path)

    def process_text(self, context):
        """
        Processes text
        :param context: dict
        :return: None
        """
        self.logger.debug("Text detected")
        try:
            if context["from"]["id"] in self.file_history:
                file_id = context["from"]["id"]
                if context["text"] in self.document_converter.AVAILABLE_OUTPUT_FORMATS:
                    self.convert_document(context, file_id)

                elif context["text"] in self.image_converter.AVAILABLE_FORMATS:
                    self.convert_image(context, file_id)

                elif context["text"] in self.video_converter.AVAILABLE_FORMATS:
                    self.convert_video(context, file_id)

            if "/" in context["text"]:
                self.process_command(context)
            else:
                self.send_message(context, "wrong_format")

        except UnsupportedFormatException:
            self.send_message(context, "wrong_format")
            self.logger.error("Wrong format")

    def process_message(self, context):
        """
        Processes message send by a user in telegram
        :param context: dict
        :return: None
        """
        if "document" in context:
            self.process_media(context)

        elif "text" in context:
            self.process_text(context)

        if "photo" in context or "video" in context:
            self.send_message(context, "compressed_file")
            self.logger.debug("Compressed file supplied")
