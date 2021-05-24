from datetime import datetime as dt, timedelta

from flask import request, session
from flask_socketio import emit, join_room, leave_room, close_room
from pymongo import ReturnDocument

from project import socket_io, mongo
from project.sub_functions import user_management, disconnect_students


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

    user_management(client_id=request.sid, room_id=room_id, user_name=username)

    # TODO: Add participant count as they join
    message = f"{username} has joined the room."
    join_room(room_id)
    emit('message', message, to=room_id, include_self=False, namespace='/meeting')


# Leave room
@socket_io.on('leave-room', namespace='/meeting')
def on_leave(data):
    room_id = data['room_id']
    username = data['user_id']

    meeting_collection = mongo.get_collection("meetings")
    meeting_collection.find_one_and_update({"meeting_id": room_id},
                                           {"$set": {
                                               f"attendance_records.{request.sid}.1": "left",
                                               f"attendance_records.{request.sid}.3": dt.now().isoformat()}})
    # TODO: Remove participant count as they leave

    message = f"{username} has left the room."
    leave_room(room_id)
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
    meeting_data = meeting_collection.find_one_and_update(
        {f"attendance_records.{request.sid}": {"$exists": 1}},  # the $exists operator checks for existence
        {"$set": {
            f"attendance_records.{request.sid}.1": "left",
            f"attendance_records.{request.sid}.3": left_at
        }},
        {"meeting_id": 1, f"attendance_records.{request.sid}": 1,
         "status": 1, "meeting_start_dateTime": 1,
         "meeting_duration": 1},
        return_document=ReturnDocument.AFTER
    )
    room_id = meeting_data["meeting_id"]
    username = meeting_data["attendance_records"][f"{request.sid}"][0]
    message = f"{username} has left the room."
    # clear session
    session.pop('USERNAME', None)
    emit('message', message, to=room_id, include_self=False, namespace='/meeting')
    if username == "Host":
        duration = meeting_data["meeting_duration"]
        start_datetime = meeting_data["meeting_start_dateTime"]
        end_datetime = start_datetime + timedelta(seconds=duration)

        # If meeting time is not up but host exits meeting due to network failures or computer issues
        if (time_stopped := dt.now()) < end_datetime:
            duration_remaining = duration - (time_stopped - start_datetime).seconds
            meeting_collection.find_one_and_update({"meeting_id": room_id},
                                                   {"$set": {"duration_left": duration_remaining,
                                                             "status": "pending", "is_verified": False}})
            # clear session
            session.pop('OTP', None)
            session.clear()
        disconnect_students(room_id=room_id)  # disconnect all users
        close_room(room_id)

# User leaving by closing browser tab. Write that js prompt to ask users if they want to leave a site
# In this case if a user clicks on the Leave site button we trigger the leave room handle
