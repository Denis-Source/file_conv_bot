import json
import os
import requests

from src.logger import Logger
from config import Config
from src.converters import image_converter, video_coverter, document_converter
from src.converters.converter import UnsupportedFormatException
from src.database.database import DataBase, UserIsAlreadyRegistered


class Bot(Config):
    """
    Bot class used for documents, images and videos conversion
    """
    TELEGRAM_API = "https://api.telegram.org"

    def __init__(self, lang="eng"):
        self.phrases_file = "phrases.json"
        self.lang = lang

        self.image_converter = image_converter.ImageConverter()
        self.video_converter = video_coverter.VideoConverter()
        self.document_converter = document_converter.DocumentConverter()
        self.database = DataBase()

        self.logger = Logger("bot")
        self.logger.info("Bot started")

        self.text_data = self.read_phrases()
        self.database.set_admin(self.ADMIN_TELEGRAM_ID)

    def read_phrases(self):
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
            response = self.get_answer(message)
            log_response = message
        else:
            response = message
            log_response = "other"
        data = {"chat_id": context["from"]["id"],
                "text": response}
        requests.post(url=self.get_url("sendMessage"), data=data)
        self.logger.info(f"Message {log_response} sent to {context['from']['id']}")

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
            self.database.inc_stat(context["from"]["id"])
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

    def process_image(self, context, image_format):
        """
        Sends message about image formats
        :param image_format: str
        :param context: dict
        :return: None
        """
        available_formats = self.image_converter.AVAILABLE_FORMATS.copy()
        available_formats.remove(image_format)
        self.logger.debug("Document with supported image format detected")
        self.send_message(context, "image_detected")
        self.send_message(context,
                          ", ".join(available_formats), is_phrase=False)

    def process_document(self, context, document_format):
        """
        Sends message about document formats
        :param document_format: str
        :param context: dict
        :return: None
        """
        available_formats = self.document_converter.AVAILABLE_OUTPUT_FORMATS.copy()
        available_formats.remove(document_format)
        self.logger.debug("Document with supported document format detected")
        self.send_message(context, "document_detected")
        self.send_message(context,
                          ", ".join(available_formats), is_phrase=False)

    def process_video(self, context, video_format):
        """
        Sends message about video formats
        :param video_format: str
        :param context: dict
        :return: None
        """
        available_formats = self.video_converter.AVAILABLE_FORMATS.copy()
        available_formats.remove(video_format)
        self.logger.debug("Document with supported video format detected")
        self.send_message(context, "video_detected")
        self.send_message(context,
                          ", ".join(available_formats), is_phrase=False)

    def process_media(self, context):
        """
        Processes media if document is received
        If a document was received firstly tries to delete the previous assigned file path
        Sets a new file path
        Downloads the document and stores it in a temporary folder
        Recognizes a file format and calls the corresponding answer function
        :param context: dict
        :return: None
        """
        if "document" in context:
            self.logger.debug("Document detected")

            file_id = context["document"]["file_id"]
            old_path = self.document_converter.find_file_by_id(
                self.database.get_filepath(
                    context["from"]["id"]
                )
            )
            try:
                os.remove(old_path)
            except Exception as e:
                self.logger.info(f"Error deleting file at {old_path}: {e}")

            self.database.set_filepath(
                context["from"]["id"],
                file_id
            )

            document_path = self.download_document(file_id)
            file_format = document_path.split(".")[-1]

            if file_format in self.image_converter.AVAILABLE_FORMATS:
                self.process_image(context, file_format)

            elif file_format in self.document_converter.AVAILABLE_INPUT_FORMATS:
                self.process_document(context, file_format)

            elif file_format in self.video_converter.AVAILABLE_FORMATS:
                self.process_video(context, file_format)

            else:
                self.logger.debug(f"Document format {file_format} not supported")
                self.send_message(context, "not_supported_format")

    def command_start(self, context):
        """
        Sends start answer
        :param context: dict
        :return: None
        """
        self.send_message(context, "start")

    def command_formats(self, context):
        message = f"{self.get_answer('available_formats')}\n\n" \
                  f"{self.get_answer('available_formats_images')}\n" \
                  f"{', '.join(self.image_converter.AVAILABLE_FORMATS)}\n\n" \
                  f"{self.get_answer('available_formats_documents')}\n" \
                  f"{', '.join(self.document_converter.AVAILABLE_INPUT_FORMATS)}\n\n" \
                  f"{self.get_answer('available_formats_video')}\n" \
                  f"{', '.join(self.video_converter.AVAILABLE_FORMATS)}"
        self.send_message(context, message, is_phrase=False)

    def command_register(self, context):
        """
        Registers an user in database
        Checks whether an user has needed privileges
        If so parses a message to get a new user id
        If no proper user id supplied or an user is already registered
        sends a corresponding message
        :param context: dict
        :return: None
        """
        user_id = context["from"]["id"]
        if self.database.get_admin(user_id):
            text = context["text"]
            if len(text.split(" ")) == 2:
                _, new_user = text.split(" ")
                try:
                    new_user = int(new_user)
                    self.database.register_user(new_user)
                    self.send_message(context, "user_registered")
                    self.logger.warning(f"New user {new_user} registered")
                except ValueError:
                    self.send_message(context, "not_valid_user")
                except UserIsAlreadyRegistered:
                    self.send_message(context, "user_already_registered")
            else:
                self.send_message(context, "wrong_command_format")
        else:
            self.send_message(context, "user_not_admin")

    def process_command(self, context):
        """
        Calls a necessary command function
        :param context: dict
        :return: None
        """
        if "/start" in context["text"]:
            self.command_start(context)
        elif "/formats" in context["text"]:
            self.command_formats(context)
        elif "/register" in context["text"]:
            self.command_register(context)
        else:
            self.send_message(context, "wrong_command")

    def convert_image(self, context, file_id):
        """
        Converts and sends received image
        :param context: dict
        :param file_id: str
        :return: None
        """
        self.send_message(context, "converting_image")
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
        self.send_message(context, "converting_document")
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
        self.send_message(context, "converting_video")
        file_path = self.video_converter.find_file_by_id(file_id)
        old_format = file_path.split(".")[-1]
        if old_format in self.video_converter.AVAILABLE_FORMATS:  # TODO
            if context["text"] == "frame":
                new_file_path = self.video_converter.frame_video(file_path)
                self.send_document(context, new_file_path)
                self.logger.debug("Video conversion successful")
                self.video_converter.delete_file(new_file_path)
            else:
                # TODO
                self.send_message(context, "dev_feature")

    def process_file_format(self, context):
        """
        If supported format supplied and user is authorized converts document
        :param context: dict
        :return: None
        """
        if self.database.get_authorised(telegram_id=context["from"]["id"]):
            prev_file_path = self.database.get_filepath(context["from"]["id"])
            if prev_file_path:
                text = context["text"].lower()
                if text in self.document_converter.AVAILABLE_OUTPUT_FORMATS:
                    self.convert_document(context, prev_file_path)

                elif text in self.image_converter.AVAILABLE_FORMATS:
                    self.convert_image(context, prev_file_path)

                elif text in self.video_converter.AVAILABLE_FORMATS:
                    self.convert_video(context, prev_file_path)

                else:
                    self.send_message(context, "not_supported_format")
            else:
                self.send_message(context, "no_file")
        else:
            self.send_message(context, "unknown_user")

    def process_text(self, context):
        """
        Processes text
        If a command detected processes command
        Else treats a message as a conversion format request
        :param context: dict
        :return: None
        :raises: UnsupportedFormatException
        """
        self.logger.debug("Text detected")
        try:
            if "/" in context["text"]:
                self.process_command(context)
            else:
                self.process_file_format(context)

        except UnsupportedFormatException:
            self.send_message(context, "wrong_format")
            self.logger.error("Wrong format")

    def process_message(self, context):
        """
        Processes message send by a user in telegram
        Recognises a message attachment and processes it accordingly
        :param context: dict
        :return: None
        """
        try:
            if "text" in context:
                self.process_text(context)
            else:
                if self.database.get_authorised(telegram_id=context["from"]["id"]):
                    if "document" in context:
                        if context["document"]["file_size"] <= 2000000:
                            self.process_media(context)
                        else:
                            self.send_message(context, "file_too_big")

                    elif "photo" in context or "video" in context:
                        self.send_message(context, "compressed_file")

                    elif "sticker" in context:
                        # TODO sticker
                        self.send_message(context, "dev_feature")

                    elif "animation" in context:
                        # TODO animation
                        self.send_message(context, "dev_feature")

                    elif "audio" in context:
                        self.send_message(context, "dev_feature")
                        # TODO audio
                    else:
                        self.send_message(context, "unsupported_message_type")
                else:
                    self.send_message(context, "unknown_user")
        except Exception as e:
            self.send_message(context, "error")
            self.logger.error(e)
