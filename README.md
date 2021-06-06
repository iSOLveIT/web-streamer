# **ONLINE LECTURE PLATFORM**

#### **`Authors Randy and Karen`**

Celery Worker command = celery -A project.celery worker --loglevel=info
Redis Server = redis-server
GUnicorn =  gunicorn -w 1 -k eventlet --reload -b 127.0.0.1:8000 app:application

