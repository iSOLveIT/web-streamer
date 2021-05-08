from datetime import datetime as dt

from flask import request
from flask_socketio import emit, join_room, leave_room

from project import socket_io
from project import mongo


# Client Connected
@socket_io.on('connect', namespace='/meeting')
def test_connect():
    emit('server_response', {'result': 'Connected!'},
         to=request.sid, namespace='/meeting')


# Room Broadcasting message to all room clients excluding the sender
@socket_io.on('send_room_message', namespace='/meeting')
def handle_room_broadcast_message(message):
    room_id = message['room_id']
    msg = message['msg']
    sent_by = message['sender']
    emit('receive_room_message', {'sender': sent_by, 'msg': msg}, to=room_id,
         include_self=False, namespace='/meeting')


# JOINING AND LEAVING ROOM
# Join Room
@socket_io.on('join-room', namespace='/meeting')
def on_join(data):
    room_id = data['room_id']
    username = data['user_id']
    join_room(room_id)

    joined_at = dt.now().isoformat()
    # Add user to students records in DB
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find_one({"meeting_id": room_id}, {"attendance_records": 1})
    attendance_records: dict = meeting_data['attendance_records']

    message = f"{username} has rejoined the room."

    if username not in attendance_records.keys():
        attendance_records.update([(request.sid, [username, joined_at, ""])])
        meeting_collection.find_one_and_update({"meeting_id": room_id},
                                               {"$set": {"attendance_records": attendance_records}})
        message = f"{username} has joined the room."
    # TODO: Add participant count as they join
    emit('message', message, to=room_id, include_self=False, namespace='/meeting')


# Leave room
@socket_io.on('leave-room', namespace='/meeting')
def on_leave(data):
    room_id = data['room_id']
    username = data['user_id']
    leave_room(room_id)

    left_at = dt.now().isoformat()
    meeting_collection = mongo.get_collection("meetings")
    meeting_collection.find_one_and_update({"meeting_id": room_id},
                                           {"$set": {f"attendance_records.{request.sid}.2": left_at}})
    message = f"{username} has left the room."
    # TODO: Remove participant count as they leave
    emit('message', message, to=room_id, include_self=False, namespace='/meeting')


# Client Disconnected
@socket_io.on('disconnect', namespace='/meeting')
def test_disconnect():
    # User leaving by closing browser tab or refreshing.
    left_at = dt.now().isoformat()
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find_one_and_update({f"attendance_records.{request.sid}": {"$exists": 1}},
                                                          {"$set": {f"attendance_records.{request.sid}.2": left_at}},
                                                          {"meeting_id": 1, f"attendance_records.{request.sid}": 1}
                                                          )
    room_id = meeting_data["meeting_id"]
    username = meeting_data["attendance_records"][f"{request.sid}"][0]
    message = f"{username} has left the room."
    emit('message', message, to=room_id, include_self=False, namespace='/meeting')
    # User leaving by closing browser tab. Write that js prompt to ask users if they want to leave a site
    # In this case if a user clicks on the Leave site button we trigger the leave room handle
