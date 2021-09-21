# ONLINE LECTURE PLATFORM

[iSTREAM](https://www.istream.cam) online video lecturing platform for UPSA

## Prerequisites

Setup Ant Media Server
* Visit [Ant Media's Github Wiki](https://github.com/ant-media/Ant-Media-Server/wiki/Installation)


Install Python 3
```bash
$ sudo apt-get install python3.9 python3-pip
```

Change to app directory
```bash
$ cd istream-app
```

Install Python virtual environment package
```bash
$ pip3 install venv
```

Create and activate virtual environment
```bash
$ python3.9 -m venv .
$ source bin/activate
```

Install required packages for the app
```bash
$ pip install -r requirements.txt
```

Start Mongo Database  
```bash
$ systemctl start mongod
```

Start Redis Server
``` bash
$ redis-server
```

Start Celery Worker 
``` bash
$ celery -A project.celery worker --loglevel=info
```

Start Gunicorn 
``` bash
$ gunicorn -w 1 -k eventlet --reload -b 127.0.0.1:8000 app:application
```

**:octocat: Authors: 👨‍💻 Randy Duodu and 👩‍💻 Karen Ackom**
