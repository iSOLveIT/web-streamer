from datetime import datetime as dt

from flask import flash, redirect, request, session, url_for
from flask_socketio import close_room, emit, join_room, leave_room
from pymongo import ReturnDocument

from project import mongo, socket_io
from project.sub_functions import disconnect_students, user_management


# Client Connected
@socket_io.on('connect', namespace='/meeting')
def test_connect():
    emit('server_response', {'result': 'Connected to room'},
         to=request.sid, namespace='/meeting')


# Send Notification
@socket_io.on('notice', namespace='/meeting')
def notification(message):
    room_id = message['room_id']
    msg = message['msg']
    emit('room_notice', msg, to=room_id, include_self=False, namespace='/meeting')


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
    user_id = data['user_id']
    display_name = data['user_name']

    participants = user_management(client_id=request.sid, room_id=room_id,
                                   user_id=user_id, user_name=display_name)

    message = f"{user_id}"
    join_room(room_id)
    emit('add_members', participants, to=request.sid, include_self=True, namespace='/meeting')
    emit('add_member', message, to=room_id, include_self=False, namespace='/meeting')


# Leave room
@socket_io.on('leave-room', namespace='/meeting')
def on_leave(data):
    room_id = data['room_id']
    user_id = data['user_id']

    meeting_collection = mongo.get_collection("meetings")
    meeting_collection.find_one_and_update({"meeting_id": room_id},
                                           {"$set": {
                                               f"attendance_records.{request.sid}.1": "left",
                                               f"attendance_records.{request.sid}.3": dt.now().strftime("%Y-%m-%d %H:%M")}})

    message = f"{user_id}"
    leave_room(room_id)
    session.pop('USER_ID', None)
    emit('remove_member', message, to=room_id, include_self=False, namespace='/meeting')


# Close and delete room
@socket_io.on('close-room', namespace='/meeting')
def on_close(data):
    room_id = data['room_id']
    user_id = data['user_id']

    if user_id == "Host":
        session.pop('OTP', None)
        emit('class_end', to=room_id, include_self=False, namespace='/meeting')  # Handles redirecting students
        disconnect_students(room_id=room_id)  # disconnect all users
        leave_room(room_id)
        close_room(room_id)


# Client Disconnected
@socket_io.on('disconnect', namespace='/meeting')
def test_disconnect():
    # User leaving by closing browser tab or refreshing.
    left_at = dt.now().strftime("%Y-%m-%d %H:%M")
    meeting_collection = mongo.get_collection("meetings")
    # if a user leaves class
    meeting_data = meeting_collection.find_one_and_update(
        {f"attendance_records.{request.sid}": {"$exists": 1}},  # the $exists operator checks for existence
        {"$set": {
            f"attendance_records.{request.sid}.1": "left",
            f"attendance_records.{request.sid}.3": left_at
        }},
        {"meeting_id": 1, f"attendance_records.{request.sid}": 1,
         "status": 1, "meeting_start_dateTime": 1,
         "meeting_end_dateTime": 1},
        return_document=ReturnDocument.AFTER
    )

    room_id = meeting_data["meeting_id"]
    user_id = meeting_data["attendance_records"][f"{request.sid}"][0]
    message = f"{user_id}"
    emit('remove_member', message, to=room_id, include_self=False, namespace='/meeting')

    if user_id == "Host":
        start_datetime = meeting_data["meeting_start_dateTime"]
        end_datetime = meeting_data['meeting_end_dateTime']

        # If meeting time is not up but host exits meeting due to network failures or computer issues
        # Disconnect everyone and allow them to rejoin again
        if start_datetime <= dt.now() < end_datetime:
            duration_remaining = (end_datetime - dt.now()).seconds
            meeting_collection.find_one_and_update({"meeting_id": room_id},
                                                   {"$set": {"duration_left": duration_remaining,
                                                             "status": "pending", "is_verified": False}})
            emit('class_end', to=room_id, include_self=False, namespace='/meeting')     # Handles redirecting students
            disconnect_students(room_id=room_id)  # disconnect all users
            close_room(room_id)
            flash(message="Class ended before time. Please restart the class if you are the Host.", category="notice")
            return redirect(url_for('all_verification', loader="host_verify"))

        meeting_collection.find_one_and_update({"meeting_id": room_id},
                                               {"$set": {"status": "expired", "duration_left": 0}})

        emit('class_end', to=room_id, include_self=False, namespace='/meeting')     # Handles redirecting students
        disconnect_students(room_id=room_id)  # disconnect all users
        close_room(room_id)
        flash(message="Class has ended.", category="notice")
        return redirect(url_for('index'))


# User leaving by closing browser tab.
