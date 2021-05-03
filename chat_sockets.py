from random import sample

from flask import request
from flask_socketio import emit, join_room, leave_room

from project import socket_io


# SOCKET_IO CODE
clients = {}
rooms_clients = {}


@socket_io.on('connect', namespace='/room')
def test_connect():
    emit('server_response', {'result': 'Connected!'},
         to=request.sid, namespace='/room')


# Storing Credentials for a client
@socket_io.on('store_user_credential', namespace='/room')
def handle_credentials(data):
    user_id = data['client_id']
    if user_id not in clients.values():
        num = sample(range(1, 2000), 1)
        clients.update([(f'user_{num[0]}', user_id)])

    username = [i for i, j in clients.items() if request.sid == j][0]
    emit('username', username, to=request.sid, namespace='/room')
    emit('server_response', {'result': 'Credentials stored!'},
         to=request.sid, namespace='/room')


# Storing Credentials for a room and its client
@socket_io.on('store_room_user_credential', namespace='/room')
def handle_room_credentials(data):
    room_id = data['room_id']
    user_socket_id = data['client_id']
    get_client_name = [i for i, j in clients.items() if user_socket_id == j]
    username = get_client_name[0]

    if room_id not in rooms_clients.keys():
        body = (room_id, [
            {'user_socketID': user_socket_id, 'username': username}
        ])
        rooms_clients.update([body])
    else:
        get_room = rooms_clients.get(room_id)
        body = {'user_socketID': user_socket_id, 'username': username}
        get_room.append(body)

    emit('server_response', {'result': f'User credentials stored for room_{room_id}!'},
         to=request.sid, namespace='/room')


# Room Broadcasting message to all room clients excluding the sender
@socket_io.on('send_room_message', namespace='/room')
def handle_room_broadcast_message(message):
    room_id = message['room_id']
    msg = message['msg']
    sent_by = message['sender']
    emit('receive_room_message', {'sender': sent_by, 'msg': msg}, to=room_id,
         include_self=False, namespace='/room')


# JOINING AND LEAVING ROOM
@socket_io.on('join-room', namespace='/room')
def on_join(data):
    user_socket_id = data['client_id']
    room_id = data['room_id']
    get_client_name = [i for i, j in clients.items() if user_socket_id == j]
    username = get_client_name[0]
    join_room(room_id)
    message = f"{username} has joined the room."
    emit('message', message, to=room_id, include_self=False, namespace='/room')


@socket_io.on('leave-room', namespace='/room')
def on_leave(data):
    user_socket_id = data['client_id']
    room_id = data['room_id']
    # get_client_name = [i for i, j in clients.items() if user_socket_id == j]
    # username = get_client_name[0]

    username = ""
    leave_room(room_id)
    # user_socket_id = clients.pop(username)  # Remove client from clients data
    get_room = rooms_clients.get(room_id)  # returns list
    for i in get_room:  # returns dictionary
        if i['user_socketID'] == user_socket_id:
            username = i['username']
            get_room.remove(i)  # Remove client from room data

    rooms_clients[room_id] = get_room
    message = f"{username} has left the room."
    emit('message', message, to=room_id, include_self=False, namespace='/room')


# Todo: Create a rejoin event to handle room reconnections


# CLIENT DISCONNECTED
@socket_io.on('disconnect', namespace='/room')
def test_disconnect():
    print(f"Client {request.sid} disconnected!")
