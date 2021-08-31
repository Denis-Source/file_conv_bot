from src.logger import Logger
from src.converters.converter import Converter


class BotFileHistory(dict, Converter):
    """
    Bot history class
    Tracks filenames downloaded from chats in a temporary folder
    Stores one file per chat
    Required to store a file downloaded in the previous message
    Based on a builtin dict and a Converter classes
    """
    def __init__(self):
        super().__init__()
        self.logger = Logger("bot_hist")

    def __setitem__(self, key, value):
        """
        When key overrides deletes file, that has been stored previously
        If new key supplied does nothing new
        :param key: any
        :param value: any
        :return: any
        """
        try:
            prev_value = self[key]
            prev_file = self.find_file_by_id(prev_value)
            self.delete_file(prev_file)
        except KeyError:
            pass
        return super(BotFileHistory, self).__setitem__(key, value)

