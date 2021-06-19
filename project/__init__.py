# Authors Randy Duodu and Karen Ackom
import os
from zoneinfo import ZoneInfo

import redis
from celery import Celery
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_compress import Compress
from flask_mail import Mail
from flask_session import Session
from flask_socketio import SocketIO
from pymongo import MongoClient
from pathlib import Path
from dotenv import load_dotenv


application = Flask(__name__)

# Session Configuration
application.config['SESSION_COOKIE_NAME'] = "istream"
application.config['SESSION_COOKIE_PATH '] = "/"
application.config['SESSION_COOKIE_SECURE'] = True
application.config['SESSION_COOKIE_HTTPONLY'] = True
application.config['SESSION_COOKIE_SAMESITE'] = "Lax"
application.config['PERMANENT_SESSION_LIFETIME'] = 10800  # Expiration time for session (3 hours)

# Config and Instantiate Mongo
client = MongoClient(host="localhost", port=18000)
mongo = client.get_database(name="vCLASS")

# Load env variables
env_path: Path = Path('.').resolve().joinpath('project/configure', 'app_keys.env')
load_dotenv(dotenv_path=str(env_path))

# Config Mail
application.config['MAIL_SERVER'] = 'smtp.gmail.com'
application.config['MAIL_PORT'] = 465
application.config['MAIL_USE_SSL'] = True
application.config['MAIL_USE_TLS'] = False
application.config['MAIL_USERNAME'] = str(os.getenv("MAIL_USERNAME"))
application.config['MAIL_PASSWORD'] = str(os.getenv("MAIL_PASSWORD"))
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
                                            'application/x-font-ttf', 'font/opentype', 'font/x-woff', 'image/svg+xml', 'font/sfnt', 'application/octet-stream']
application.config['COMPRESS_BR_LEVEL'] = 9

Compress(application)  # Instantiate Flask Compress into app


# Flask Session Config
application.config['SESSION_TYPE'] = "redis"
application.config['SESSION_REDIS'] = redis.Redis(host='localhost', port=8379, db=0)
Session(application)

# Flask CSRF Protection
csrf = CSRFProtect(application)
application.config['WTF_CSRF_SECRET_KEY'] = os.urandom(23)

# Meeting Timezone
gh = ZoneInfo("GMT")


# SocketIO Config
socket_io = SocketIO(application, manage_session=False, cors_allowed_origins=["https://istream.cam","https://www.istream.cam","http://istream.cam", "http://www.istream.cam"])

# Security measures
@application.after_request
def set_secure_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "upgrade-insecure-requests; default-src https://*.istream.cam; style-src 'self' https: 'unsafe-inline'; font-src https: ; frame-src 'self' https://*.istream.cam/LiveApp/ blob: mediastream:; script-src 'self' 'unsafe-inline' blob: https:; img-src 'self' https: data:; connect-src 'self' https://istream.cam/socket.io; media-src 'self' https:;"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

from project import chat_sockets, error_routes, routes
