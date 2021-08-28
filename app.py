from flask import Flask
from flask_restful import Api

from src.api import BotResource
from config import Config

app = Flask(__name__)
api = Api(app)

if __name__ == '__main__':
    api.add_resource(BotResource, "/")
    app.run(host="0.0.0.0", port=Config.SERVER_PORT)
