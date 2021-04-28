from flask import render_template, request, redirect, url_for
from random import sample
from string import ascii_letters
from project import app


room_store = {}


@app.route('/')
def index():
    return render_template('user_pages/index.html')


@app.route('/room/<string:stream_id>')
def studio(stream_id):
    broadcast_viewer = request.args.get('viewer')
    if broadcast_viewer == "broadcast":
        alphanum = ascii_letters + '0123456789'
        room_id = ''.join(sample(alphanum, 7))
        room_store.update([(stream_id, room_id)])
        return render_template('stream_pages/studio.html', stream_id=stream_id, room_id=room_id)
    elif broadcast_viewer == "stream":
        room_id = room_store.get(stream_id)
        return render_template('stream_pages/viewers.html',
                               stream_id=stream_id, room_id=room_id)
    return redirect(url_for("index"))


# @app.route('/room/viewers/<string:stream_id>')
# def view_room(stream_id):
#     room_id = room_store.get(stream_id)
#     return render_template('stream_pages/viewers.html', room_id=room_id)
