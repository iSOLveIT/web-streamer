from flask import Flask
from flask_socketio import SocketIO
from pymongo import MongoClient


app = Flask(__name__)

# Session Configuration
app.config['SESSION_COOKIE_NAME'] = "istream"
app.config['SESSION_COOKIE_PATH '] = "/meeting"
# app.config['SESSION_COOKIE_SECURE'] = True
# app.config['SESSION_COOKIE_HTTPONLY'] = True
# app.config['SESSION_COOKIE_SAMESITE'] = "None"
app.config['PERMANENT_SESSION_LIFETIME'] = 10800  # Expiration time for session (3 hours)

socket_io = SocketIO(app)
# Config and Instantiate Mongo
# user = str(os.environ.get('MONGODB_USERNAME'))
# passwd = str(os.environ.get('MONGODB_PASSWORD'))
# uri = f"mongodb+srv://{user}:{passwd}@agms01-vtxt7.mongodb.net/?retryWrites=true&w=majority"    # Mongo connection str
# client = MongoClient(uri, ssl=True, ssl_cert_reqs=ssl.CERT_NONE)
client = MongoClient()
mongo = client.get_database(name="vCLASS")

from project import routes, chat_sockets
