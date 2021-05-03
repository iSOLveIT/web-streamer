from flask import Flask
from flask_socketio import SocketIO
from pymongo import MongoClient


app = Flask(__name__)
socket_io = SocketIO(app)
# Config and Instantiate Mongo
# user = str(os.environ.get('MONGODB_USERNAME'))
# passwd = str(os.environ.get('MONGODB_PASSWORD'))
# uri = f"mongodb+srv://{user}:{passwd}@agms01-vtxt7.mongodb.net/?retryWrites=true&w=majority"    # Mongo connection str
# client = MongoClient(uri, ssl=True, ssl_cert_reqs=ssl.CERT_NONE)
client = MongoClient()
mongo = client.get_database(name="vCLASS")

from project import chat_sockets, routes
