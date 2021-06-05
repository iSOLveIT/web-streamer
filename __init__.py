from zoneinfo import ZoneInfo

from celery import Celery
from flask import Flask
from flask_compress import Compress
from flask_mail import Mail
from flask_socketio import SocketIO
from pymongo import MongoClient


application = Flask(__name__)

# Session Configuration
application.config['SESSION_COOKIE_NAME'] = "istream"
application.config['SESSION_COOKIE_PATH '] = "/meeting"
# app.config['SESSION_COOKIE_SECURE'] = True
application.config['SESSION_COOKIE_HTTPONLY'] = True
application.config['SESSION_COOKIE_SAMESITE'] = "Lax"
application.config['PERMANENT_SESSION_LIFETIME'] = 10800  # Expiration time for session (3 hours)

socket_io = SocketIO(application)
# Config and Instantiate Mongo
# user = str(os.environ.get('MONGODB_USERNAME'))
# passwd = str(os.environ.get('MONGODB_PASSWORD'))
# uri = f"mongodb+srv://{user}:{passwd}@agms01-vtxt7.mongodb.net/?retryWrites=true&w=majority"    # Mongo connection str
# client = MongoClient(uri, ssl=True, ssl_cert_reqs=ssl.CERT_NONE)
# mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false
client = MongoClient()
mongo = client.get_database(name="vCLASS")

# Config Mail
application.config['MAIL_SERVER'] = 'smtp.gmail.com'
application.config['MAIL_PORT'] = 465
application.config['MAIL_USE_SSL'] = True
application.config['MAIL_USE_TLS'] = False
application.config['MAIL_USERNAME'] = "isolveitgroup@gmail.com"
application.config['MAIL_PASSWORD'] = "jbbtgtiihrqzssah"
application.config['MAIL_MAX_EMAILS'] = 1000

mail = Mail(application)

# Config Celery
application.config['CELERY_BROKER_URL'] = 'redis://localhost:8379/0'
celery = Celery(application.name, broker=application.config['CELERY_BROKER_URL'])
celery.conf.update(application.config)

# Configure Flask Compress
# Types of files to compress
application.config['COMPRESS_MIMETYPES'] = ['text/html', 'text/css', 'text/javascript', 'application/javascript',
                                            'application/json', 'application/vnd.ms-fontobject', 'image/svg+xml',
                                            'font/ttf', 'font/woff', 'font/woff2', 'application/x-javascript',
                                            'text/xml', 'application/xml', 'application/xml+rss', 'image/x-icon',
                                            'application/x-font-ttf', 'font/opentype', 'font/x-woff', 'image/svg+xml']
application.config['COMPRESS_BR_LEVEL'] = 5

Compress(application)  # Instantiate Flask Compress into app

# Meeting Timezone
gh = ZoneInfo("GMT")


from project import chat_sockets, error_routes, routes
