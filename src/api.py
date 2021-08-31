from flask_restful import Resource, abort
from flask_restful.reqparse import RequestParser
from src.bot.bot import Bot


class BotResource(Resource):
    """
    Api class to handle telegram bot api
    """
    BOT_INSTANCE = Bot()

    def __init__(self):
        super().__init__()

    def post(self):
        """
        Handles a post request from telegram bot api
        :return: dict
        """
        parser = RequestParser()
        parser.add_argument("message", type=dict)
        data = parser.parse_args()
        if data["message"]:
            message = data["message"]
            self.BOT_INSTANCE.process_message(message)
        return {"ok": True}
