import os

from project import application, socket_io

application.config['SECRET_KEY'] = os.urandom(76)

if __name__ == '__main__':
    socket_io.run(application)
