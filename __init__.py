from flask import Flask
from flask_socketio import SocketIO


app = Flask(__name__)
socket_io = SocketIO(app)

from project import routes
from project import chat_sockets