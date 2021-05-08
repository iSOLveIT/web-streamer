import re
from datetime import timedelta
from functools import wraps

from flask import redirect, render_template, request, url_for, session
from pymongo import ReturnDocument
from passlib.hash import oracle10

from project import app, mongo
from project.sub_functions import random_str_generator, date_and_time, sec_to_time_format


# Check if host is verified
def host_verification(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'OTP' not in session:
            return redirect(url_for('host_auth'))
        return f(*args, **kwargs)

    return decorated


# Check if meeting_id exist and user is verified
def user_verification(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'USERNAME' not in session:
            return redirect(url_for('join_meeting', join_params='details'))
        return f(*args, **kwargs)

    return decorated


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
            stream_id, meeting_id = random_str_generator(5), random_str_generator(5)
            otp = random_str_generator(4)

            prevent_idempotency = meeting_collection.find_one(
                {"$and": [
                    {"instructor": full_name},
                    {"meeting_start_dateTime": m_date_time}
                ]},
                {"attendance_records": 0, "status": 0}
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
                "attendance_records": {},
                "status": "pending",
                "is_verified": False
            })

            return f"""
<p>Instructor: {full_name}</p>
<p>Topic: {m_topic}</p>
<p>Scheduled Start Date and Time: {m_date_time.strftime('%Y-%m-%d %H:%M')}</p>
<p>Duration: {sec_to_time_format(m_duration)} hour(s)</p>
<p>Meeting ID: {meeting_id}</p>
<p>Share Link with students: <a href='http://127.0.0.1:8080/join_meeting/auto?mid={meeting_id}'> \
http://127.0.0.1:8080/join_meeting/auto?mid={meeting_id}</a><p><br>

<p><b>NB: Please don't share your meeting OTP (One-Time Password) with anyone.</b></p>
<p>Meeting OTP: {otp}</p>  
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
        meeting_details = meeting_collection.find_one_and_update(
            {"$and": [
                {'OTP': otp}, {'is_verified': False}
            ]},
            {"$set": {"is_verified": True}},
            {'meeting_id': 1, 'stream_id': 1, 'is_verified': 1},
            return_document=ReturnDocument.AFTER  # returns the updated version of the document instead
        )
        if meeting_details is not None and meeting_details['is_verified']:
            try:
                otp_hash = oracle10.hash(otp, user='isolveit')
            except TypeError:
                return {"result": "Error occurred, please try again"}
            session['OTP'] = otp_hash
            # _class_id combines meeting_id and stream_id
            _class_id = f"{meeting_details['stream_id']}{meeting_details['meeting_id']}"
            return redirect(url_for("studio", _cid=_class_id))
        return {"result": "Access Denied."}
    return render_template('main_pages/host_verify.html')


# Route for host to view broadcast studio
@app.route('/meeting/h/<string:_cid>')
@host_verification
def studio(_cid):
    stream_id, meeting_id = _cid[:5], _cid[5:]
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find_one({'meeting_id': meeting_id}, {'status': 1, 'is_verified': 1})

    # Todo: Check if meeting time is up before redirecting
    if meeting_data["status"] == "pending":
        # Update meeting status
        meeting_collection.find_one_and_update({"meeting_id": meeting_id},
                                               {"$set": {"status": "active"}})
        return render_template('stream_pages/studio.html', stream_id=stream_id, room_id=meeting_id)
    # if meeting_data["status"] == "active" and time has not expired:
    #     return {"result": "Meeting is already in session."}
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
        meeting_exist = meeting_collection.find_one({"meeting_id": meeting_id}, {"meeting_id": 1, "status": 1})

        if check_meeting_id is not None and meeting_exist is not None:
            if meeting_exist["status"] == "active":
                return redirect(url_for('user_attendance', mid=meeting_exist["meeting_id"]))
            if meeting_exist["status"] == "pending":
                # Ensures users access the meeting only when the host has started
                return {"result": "Meeting has not started."}
        return {'result': "Invalid information."}

    if join_params == "details":
        if request.method == "POST":
            meeting_id = request.form.get("mid")
            check_meeting_id = re.search("^[a-zA-Z0-9]{5}$", meeting_id)
            meeting_exist = meeting_collection.find_one({"meeting_id": meeting_id}, {"meeting_id": 1, "status": 1})

            if check_meeting_id is not None and meeting_exist is not None:
                if meeting_exist["status"] == "active":
                    return redirect(url_for('user_attendance', mid=meeting_exist["meeting_id"]))
                if meeting_exist["status"] == "pending":
                    # Ensures users access the meeting only when the host has started
                    return {"result": "Meeting has not started."}
            return {'result': "Invalid information."}

        return render_template('main_pages/join_meeting.html')  # Add error message


# Route for student details input
@app.route('/user/authentication/<string:mid>', methods=["GET", "POST"])
def user_attendance(mid):
    meeting_collection = mongo.get_collection("meetings")

    if request.method == "POST":
        meeting_data = meeting_collection.find_one({"meeting_id": mid}, {"stream_id": 1, "status": 1})
        if meeting_data is not None and meeting_data["status"] == "active":
            username = request.form.get("username", type=str)
            result = re.search(r"^10[0-9]{6}$", username)
            if username is None or result is None:
                return {"result": "Incorrect information."}

            try:
                username_hash = oracle10.hash(username, user='isolveit')
            except TypeError:
                return {"result": "Error occurred, please try again"}

            session['USERNAME'] = username_hash
            # _class_id combines meeting_id and stream_id
            _class_id = f"{meeting_data['stream_id']}{mid}"
            return redirect(url_for("viewer", uid=username, _cid=_class_id))

        return redirect(url_for('join_meeting', join_params='details'))
    return render_template('main_pages/user_verify.html')


# Route for students to view lecture platform
@app.route('/meeting/v/<string:uid>/<string:_cid>')
@user_verification
def viewer(uid, _cid):
    stream_id, meeting_id = _cid[:5], _cid[5:]
    try:
        check_username = oracle10.verify(uid, session.get('USERNAME'), user='isolveit')
        if check_username is False:
            return {"result": "Incorrect information."}

        return render_template('stream_pages/viewers.html', stream_id=stream_id, room_id=meeting_id, user_id=uid)
    except TypeError:
        return {"result": "Error occurred, please try again"}

# TODO: Route for student leaving meeting
