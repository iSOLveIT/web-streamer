import re
from datetime import datetime as dt, timedelta

from flask import redirect, render_template, request, url_for

from project import app, mongo
from project.sub_functions import random_str_generator, date_and_time, create_broadcast, sec_to_time_format


# MAIN ROUTES
# Route for Homepage
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            full_name = request.form.get("fullname")
            m_topic = request.form.get("mTopic")
            # Meeting start date and time
            m_date = request.form.get('mDate')
            m_hour = request.form.get('hour_hand', type=int)
            m_minute = request.form.get('minute_hand', type=int)
            time_fmt = request.form.get('prompt')
            # Duration
            d_hour = int(request.form.get("mHour"))

            if re.search(r"^(\d{4})-(\d{2})-(\d{2})$", m_date) is None \
                    or (m_hour is None or m_minute is None) \
                    or re.search(r"(am|pm)", time_fmt) is None:
                return {"result": "Inaccurate information."}

            m_date_time = date_and_time(_date=m_date, _time=f"{m_hour}:{m_minute}", _fmt=time_fmt)
            m_duration = timedelta(hours=d_hour).seconds

            meeting_collection = mongo.get_collection("meetings")
            meeting_id = random_str_generator(5)
            otp = random_str_generator(3)
            stream_id = create_broadcast(meeting_name=m_topic, meeting_datetime=m_date_time)

            prevent_idempotency = meeting_collection.find_one(
                {"$and": [
                    {"instructor": full_name},
                    {"meeting_start_dateTime": m_date_time}
                ]},
                {"student_records": 0, "status": 0}
            )
            if prevent_idempotency:
                return {"result": "Meeting is already scheduled"}  # Return the details of the meeting

            meeting_collection.insert_one({
                "meeting_id": meeting_id,
                "stream_id": stream_id,
                "instructor": full_name,
                "meeting_topic": m_topic,
                "meeting_start_dateTime": m_date_time,
                "meeting_duration": m_duration,
                "OTP": otp,
                "student_records": {},
                "status": "pending"
            })

            return f"""Instructor: {full_name}\n
Topic: {m_topic}\n
Scheduled Start Date and Time: {m_date_time.strftime('%Y-%m-%d %H:%M')}\n
Duration: {sec_to_time_format(m_duration)} hours\n
Meeting ID: {meeting_id}\n
Share Link with students: http://127.0.0.1:5000/join_meeting/auto?mid={meeting_id}\n\n

NB: The meeting OTP grants instructor access to lecture platform. Don't share with anyone.\n
Meeting OTP: {otp}  
"""
        except (IndexError, ValueError):
            return {"result": "Incorrect information."}
    return render_template('main_pages/index.html')


# HOST ROUTES
# Route for host authentication
@app.route('/host/authentication', methods=["GET", "POST"])
def host_auth():
    if request.method == "POST":
        otp = request.form.get("meeting_passcode")
        result = re.search(r"^[a-zA-Z0-9]{3}$", otp)
        if otp is None or result is None:
            return {"result": "Access Denied."}
        meeting_collection = mongo.get_collection("meetings")
        meeting_details = meeting_collection.find_one({'OTP': otp}, {'meeting_id': 1, 'stream_id': 1})
        if meeting_details:
            # Todo: Check if meeting time is up before redirecting
            return redirect(url_for("studio", meeting_id=meeting_details['meeting_id'],
                                    stream_id=meeting_details['stream_id']))
        return {"result": "Access Denied."}
    return render_template('main_pages/host_verify.html')


# Route for host to view broadcast studio
@app.route('/meeting/h/<string:meeting_id>/<string:stream_id>')
def studio(meeting_id, stream_id):
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find_one({'meeting_id': meeting_id}, {'status': 1})
    if meeting_data["status"] == "pending":
        # Update meeting status
        meeting_collection.find_one_and_update({"meeting_id": meeting_id},
                                               {"$set": {"status": "active"}})
        return render_template('stream_pages/studio.html', stream_id=stream_id, room_id=meeting_id)
    if meeting_data["status"] == "active":
        return {"result": "Meeting is in session."}
    return {"result": "Meeting has ended."}


# TODO: Route for host ending meeting
# TODO: Route for host printing attendance report


# STUDENTS (VIEWERS) ROUTE
# Route for joining meeting by students
@app.route('/join_meeting/<string:join_params>', methods=["GET", "POST"])
def join_meeting(join_params):
    meeting_collection = mongo.get_collection("meetings")
    if join_params == "auto":
        meeting_id = request.args.get("mid")
        check_meeting_id = re.search("^[a-zA-Z0-9]{5}$", meeting_id)

        if check_meeting_id is not None:
            meeting_exist = meeting_collection.find_one({"meeting_id": meeting_id}, {"meeting_id": 1})
            if meeting_exist is None:
                return {'result': "Meeting has expired"}
            return redirect(url_for('user_attendance', mid=meeting_exist["meeting_id"]))
        return redirect(url_for('index'))   # Link is invalid
    if join_params == "details":
        if request.method == "POST":
            meeting_id = request.form.get("mid")
            check_meeting_id = re.search("^[a-zA-Z0-9]{5}$", meeting_id)

            if check_meeting_id is not None:
                meeting_exist = meeting_collection.find_one({"meeting_id": meeting_id}, {"meeting_id": 1})
                if meeting_exist is None:
                    return {'result': "Meeting has expired"}
                return redirect(url_for('user_attendance', mid=meeting_exist["meeting_id"]))
        return render_template('main_pages/join_meeting.html')  # Add error message


# Route for student details input
@app.route('/user/authentication/<string:mid>', methods=["GET", "POST"])
def user_attendance(mid):
    meeting_collection = mongo.get_collection("meetings")
    joined_at = dt.now().isoformat()
    left_at = dt.now().isoformat()

    if request.method == "POST":
        username = request.form.get("username", type=str)
        result = re.search(r"^10[0-9]{6}$", username)
        if username is None or result is None:
            return {"result": "Incorrect information."}

        meeting_data = meeting_collection.find_one({"meeting_id": mid}, {"OTP": 0})
        student_records = meeting_data['student_records']
        student_records.update([(username, [joined_at, left_at])])
        meeting_collection.find_one_and_update({"meeting_id": mid},
                                               {"$set": {"student_records": student_records}})
        return redirect(url_for("viewer", uid=username, sid=meeting_data["stream_id"], meeting_id=mid))

    return render_template('main_pages/user_verify.html')


# Route for students to view lecture platform
@app.route('/meeting/v/<string:uid>/<string:sid>/<string:meeting_id>')
def viewer(uid, sid, meeting_id):
    result = re.search(r"^10[0-9]{6}$", uid)
    if uid is None or result is None:
        return {"result": "Incorrect information."}
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find_one({'meeting_id': meeting_id}, {'status': 1})
    if meeting_data["status"] == "active":
        return render_template('stream_pages/viewers.html', stream_id=sid, room_id=meeting_id, user_id=uid)
    if meeting_data["status"] == "pending":
        return {"result": "Meeting has not started."}
    return {"result": "Meeting has ended."}

# TODO: Route for student leaving meeting
