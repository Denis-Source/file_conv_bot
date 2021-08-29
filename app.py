from flask import Flask
from flask_restful import Api

from src.api import BotResource
from config import Config

app = Flask(__name__)
api = Api(app)
api.add_resource(BotResource, f"/{Config.BOT_TOKEN}")

if __name__ == '__main__':
    app.run()
