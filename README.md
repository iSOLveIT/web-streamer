# ONLINE LECTURE PLATFORM

iSTREAM online video lecturing platform for UPSA

## Commands to run 

Start Mongo Database  

```bash
systemctl start mongod
```


Start Redis Server

``` bash
redis-server
```

Start Celery Worker 

``` bash
celery -A project.celery worker --loglevel=info
```

Start Gunicorn 
``` bash
gunicorn -w 1 -k eventlet --reload -b 127.0.0.1:8000 app:application
```

**`Authors: Randy Duodu and Karen Ackom`**
