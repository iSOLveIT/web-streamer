from datetime import datetime as dt, timedelta

from flask import request
from flask_socketio import emit, join_room, leave_room, close_room

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

    message = f"{username} has joined the room."

    # Check if user record already exist
    for r_key, r_value in attendance_records.items():
        if r_value[0] == username:
            # If user record exist, update client_id (key)
            user_data = attendance_records.pop(f"{r_key}")   # Remove old data
            attendance_records.update([(request.sid, user_data)])   # Update user record with new client_id as key
            meeting_collection.find_one_and_update({"meeting_id": room_id},
                                                   {"$set": {"attendance_records": attendance_records}})
        else:
            attendance_records.update([(request.sid, [username, joined_at, ""])])
            meeting_collection.find_one_and_update({"meeting_id": room_id},
                                                   {"$set": {"attendance_records": attendance_records}})
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


# Close and delete room
@socket_io.on('close-room', namespace='/meeting')
def on_close(data):
    room_id = data['room_id']
    username = data['user_id']

    if username == "Host":
        emit('message', f"Meeting ended by {username}.", to=room_id, include_self=False, namespace='/meeting')
        close_room(room_id)

        meeting_collection = mongo.get_collection("meetings")
        meeting_collection.find_one_and_update({"meeting_id": room_id},
                                               {"$set": {"status": "expired"}})


# Client Disconnected
@socket_io.on('disconnect', namespace='/meeting')
def test_disconnect():
    # User leaving by closing browser tab or refreshing.
    left_at = dt.now().isoformat()
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find_one_and_update({f"attendance_records.{request.sid}": {"$exists": 1}},
                                                          {"$set": {f"attendance_records.{request.sid}.2": left_at}},
                                                          {"meeting_id": 1, f"attendance_records.{request.sid}": 1,
                                                           "status": 1, "meeting_start_dateTime": 1,
                                                           "meeting_duration": 1}
                                                          )     # the $exists operator checks for existence
    room_id = meeting_data["meeting_id"]
    username = meeting_data["attendance_records"][f"{request.sid}"][0]
    message = f"{username} has left the room."
    emit('message', message, to=room_id, include_self=False, namespace='/meeting')
    if username == "Host":
        duration = meeting_data["meeting_duration"]
        start_datetime = meeting_data["meeting_start_dateTime"]
        end_datetime = start_datetime + timedelta(seconds=duration)

        # If meeting time is not up but host exits meeting due to network failures or computer issues
        if dt.now() < end_datetime:
            duration_remaining = duration - (dt.now() - start_datetime).seconds
            meeting_collection.find_one_and_update({"meeting_id": room_id},
                                                   {"$set": {"meeting_duration": duration_remaining,
                                                             "status": "pending", "is_verified": False}})
        close_room(room_id)

# User leaving by closing browser tab. Write that js prompt to ask users if they want to leave a site
# In this case if a user clicks on the Leave site button we trigger the leave room handle
