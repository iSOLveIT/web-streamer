from datetime import datetime as dt

from flask import request
from flask_socketio import emit, join_room, leave_room

from project import socket_io
from project import mongo


# SOCKET_IO CODE
# clients = {}
# rooms_clients = {}


@socket_io.on('connect', namespace='/meeting')
def test_connect():
    emit('server_response', {'result': 'Connected!'},
         to=request.sid, namespace='/meeting')


# # Storing Credentials for a client
# @socket_io.on('store_user_credential', namespace='/room')
# def handle_credentials(data):
#     user_id = data['client_id']
#     if user_id not in clients.values():
#         num = sample(range(1, 2000), 1)
#         clients.update([(f'user_{num[0]}', user_id)])
#
#     username = [i for i, j in clients.items() if request.sid == j][0]
#     emit('username', username, to=request.sid, namespace='/room')
#     emit('server_response', {'result': 'Credentials stored!'},
#          to=request.sid, namespace='/room')
#
#
# # Storing Credentials for a room and its client
# @socket_io.on('store_room_user_credential', namespace='/room')
# def handle_room_credentials(data):
#     room_id = data['room_id']
#     user_socket_id = data['client_id']
#     get_client_name = [i for i, j in clients.items() if user_socket_id == j]
#     username = get_client_name[0]
#
#     if room_id not in rooms_clients.keys():
#         body = (room_id, [
#             {'user_socketID': user_socket_id, 'username': username}
#         ])
#         rooms_clients.update([body])
#     else:
#         get_room = rooms_clients.get(room_id)
#         body = {'user_socketID': user_socket_id, 'username': username}
#         get_room.append(body)
#
#     emit('server_response', {'result': f'User credentials stored for room_{room_id}!'},
#          to=request.sid, namespace='/room')


# Room Broadcasting message to all room clients excluding the sender
@socket_io.on('send_room_message', namespace='/meeting')
def handle_room_broadcast_message(message):
    room_id = message['room_id']
    msg = message['msg']
    sent_by = message['sender']
    emit('receive_room_message', {'sender': sent_by, 'msg': msg}, to=room_id,
         include_self=False, namespace='/meeting')


# JOINING AND LEAVING ROOM
@socket_io.on('join-room', namespace='/meeting')
def on_join(data):
    room_id = data['room_id']
    username = data['user_id']
    join_room(room_id)
    message = f"{username} has joined the room."
    emit('message', message, to=room_id, include_self=False, namespace='/meeting')


@socket_io.on('leave-room', namespace='/meeting')
def on_leave(data):
    room_id = data['room_id']
    username = data['user_id']
    leave_room(room_id)

    meeting_collection = mongo.get_collection("meetings")
    left_at = dt.now().isoformat()
    meeting_collection.find_one_and_update({"meeting_id": room_id},
                                           {"$set": {f"student_records.{username}.1": left_at}})
    message = f"{username} has left the room."
    emit('message', message, to=room_id, include_self=False, namespace='/meeting')


# CLIENT DISCONNECTED
@socket_io.on('disconnect', namespace='/meeting')
def test_disconnect():
    print(f"Client {request.sid} disconnected!")
