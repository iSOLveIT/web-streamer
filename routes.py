import re
from datetime import datetime as dt, timedelta
from functools import wraps
from random import randint

from flask import redirect, render_template, request, url_for, session
from flask_weasyprint import render_pdf
from pymongo import ReturnDocument
from passlib.hash import oracle10

from project import app, mongo
from project.sub_functions import random_str_generator, date_and_time, sec_to_time_format, disallow_join, disallow_host


# Check if host is verified
def host_verification(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'OTP' not in session:
            return redirect(url_for('host_auth')), 301
        return f(*args, **kwargs)

    return decorated


# Check if meeting_id exist and user is verified
def user_verification(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'USERNAME' not in session:
            return redirect(url_for('join_meeting', join_params='details')), 301
        return f(*args, **kwargs)

    return decorated


# Restrict access to the attendance report page
def attendance_verification(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'report' not in session:
            return redirect(url_for('search_attendance_report')), 301
        return f(*args, **kwargs)

    return decorated


# MAIN ROUTES
# Route for Homepage
@app.route('/', methods=['GET', 'POST'])
def index():
    ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    if request.method == 'POST':
        try:
            full_name = request.form.get("fullname")
            m_topic = request.form.get("mTopic")
            m_email = request.form.get("user_email")
            # Meeting start date and time
            m_date = request.form.get('mDate')
            m_hour = request.form.get('hour_hand', type=int)
            m_minute = request.form.get('minute_hand', type=int)
            time_fmt = request.form.get('prompt')
            # Duration
            d_hour = int(request.form.get("mHour"))
            m_duration = timedelta(hours=d_hour).seconds

            if re.search(r"^(\d{4})-(\d{2})-(\d{2})$", m_date) is None \
                    or (m_hour is None or m_minute is None) \
                    or re.search(r"(am|pm)", time_fmt) is None or m_duration > 10800:
                return {"result": "Inaccurate information."}

            m_date_time = date_and_time(_date=m_date, _time=f"{m_hour}:{m_minute}", _fmt=time_fmt)

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
                "meeting_email": m_email,
                "meeting_topic": m_topic,
                "meeting_start_dateTime": m_date_time,
                "meeting_duration": m_duration,
                "OTP": otp,
                "host_ip": ip_address,
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
<p>Share Link with students: <a href='http://127.0.0.1:4080/join_meeting/auto?mid={meeting_id}'> \
http://127.0.0.1:4080/join_meeting/auto?mid={meeting_id}</a><p><br>

<p><b>NB: Please don't share your meeting OTP (One-Time Password) with anyone.</b></p>
<p>Meeting OTP: {otp}</p>  
"""
        except (IndexError, ValueError):
            return {"result": "Incorrect information."}
    return render_template('main_pages/index.html')


# HOST ROUTES
# Route for host authentication
@app.route('/host/authentication', methods=["POST"])
def host_auth():
    ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    multi_hosts = disallow_host(host_ip=ip_address)
    if multi_hosts == "disallow":
        return {"result": "Another meeting by Host is in progress"}

    otp = request.form.get("meetingOTP")
    result = re.search(r"^[a-zA-Z0-9]{6}$", otp)
    if otp is None or result is None:
        return {"result": "Access Denied."}
    meeting_collection = mongo.get_collection("meetings")
    meeting_details = meeting_collection.find_one_and_update(
        {"$and": [
            {'OTP': otp}, {'is_verified': False}
        ]},
        {"$set": {"is_verified": True, "host_ip": ip_address}},
        {'meeting_id': 1, 'stream_id': 1, 'is_verified': 1},
        return_document=ReturnDocument.AFTER  # returns the updated version of the document instead
    )
    if meeting_details is not None and meeting_details['is_verified']:
        try:
            otp_hash = oracle10.hash(otp, user='isolveit')
        except TypeError:
            return {"result": "Error occurred, please try again"}
        session["OTP"] = otp_hash
        # session.permanent = True
        # _class_id combines meeting_id and stream_id
        _class_id = f"{meeting_details['stream_id']}{meeting_details['meeting_id']}"
        return redirect(url_for("studio", _cid=_class_id))
    return {"result": "Access Denied."}


# Route for host to view broadcast studio
@app.route('/meeting/h/<string:_cid>')
@host_verification
def studio(_cid):
    stream_id, meeting_id = _cid[:5], _cid[5:]
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find_one({'meeting_id': meeting_id},
                                               {'status': 1, 'is_verified': 1, 'OTP': 1, 'instructor': 1,
                                                'meeting_start_dateTime': 1, 'meeting_duration': 1})
    meeting_end_date = meeting_data['meeting_start_dateTime'] + timedelta(seconds=meeting_data['meeting_duration'])
    check_otp = oracle10.verify(meeting_data['OTP'], session.get("OTP"), user='isolveit')

    # Todo: Check if meeting time is up before redirecting
    if check_otp is True:
        if meeting_data["status"] == "pending" and dt.now() < meeting_end_date:
            # Update meeting status
            meeting_collection.find_one_and_update({"meeting_id": meeting_id},
                                                   {"$set": {"status": "active", "is_verified": True}})
            session["report"] = randint(1, 10000)  # session for accessing attendance report page
            # session.permanent = True
            return render_template('stream_pages/studio.html', stream_id=stream_id,
                                   room_id=meeting_id, user_id="Host", user_name=meeting_data['instructor'])
        # If meeting host has login and meeting has not expired and is not the meeting from the same computer
        if meeting_data["status"] == "active" and meeting_data['is_verified'] is True and dt.now() < meeting_end_date:
            session["report"] = randint(1, 10000)  # session for accessing attendance report page
            # session.permanent = True
            return render_template('stream_pages/studio.html', stream_id=stream_id,
                                   room_id=meeting_id, user_id="Host", user_name=meeting_data['instructor'])
        return {"result": "Meeting has ended."}
    return {"result": "Access Denied."}


# TODO: Route for host ending meeting
# Route for searching and printing attendance report
@app.route('/search_attendance_report', methods=['GET', 'POST'])
def search_attendance_report():
    meeting_collection = mongo.get_collection("meetings")

    if request.method == "POST":
        search_term = request.form.get("search_term")
        result = re.search(r"^[a-zA-Z0-9]{3}$", search_term)
        if search_term is None or result is None:
            return {"result": "No results."}
        meeting_data = meeting_collection.find_one({"$and": [{'OTP': search_term}, {'status': 'expired'}]},
                                                   {'meeting_id': 1})
        if meeting_data is None:
            return {"result": "No results."}
        session['report'] = randint(1, 10000)
        # session.permanent = True
        return redirect(url_for("attendance_report", _mid=meeting_data["meeting_id"]))
    return render_template('search_report.html')


# Route for host printing attendance report
@app.route('/attendance_report/<string:_mid>')
@attendance_verification
def attendance_report(_mid):
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find_one({"meeting_id": _mid},
                                               {'status': 0, 'is_verified': 0, 'OTP': 0, 'stream_id': 0, '_id': 0})
    attendance: dict = meeting_data["attendance_records"]
    duration = meeting_data["meeting_duration"]
    start_datetime = meeting_data["meeting_start_dateTime"]
    end_datetime = start_datetime + timedelta(seconds=duration)
    meeting_details = [meeting_data["meeting_topic"], meeting_data["instructor"], start_datetime, end_datetime]
    return render_template('attendance_report.html', attendance=attendance.values(), m_details=meeting_details)


@app.route('/print_report/<string:_mid>_<string:_current>.pdf',
           defaults={'_current': dt.now().strftime('%Y%m%d%H%M')})
@attendance_verification
def print_report_pdf(_mid, _current):
    # Make a PDF from another view
    return render_pdf(url_for('attendance_report'))


#  BOTH STUDENT AND HOST ROUTES
@app.route('/verification_handle/<string:loader>')
def all_verification(loader):
    result = re.search(r"(host_verify|user_verify)", loader)
    if result is None:
        return redirect(url_for('index')), 301
    return render_template('verification.html', load=loader)


# STUDENTS (VIEWERS) ROUTE
# Route for student details input
@app.route('/user/authentication/<string:mid>', methods=["POST"])
def user_attendance(mid):
    meeting_id = request.form.get("mid")
    display_name = request.form.get("display_name")
    username: str = request.form.get("user_id", default="")
    result = username.isdigit()

    meeting_collection = mongo.get_collection("meetings")
    check_meeting_id = re.search("^[a-zA-Z0-9]{5}$", meeting_id)

    if check_meeting_id is not None and not result:
        meeting_exist = meeting_collection.find_one({"meeting_id": mid}, {"stream_id": 1, "status": 1})
        if meeting_exist is not None:
            if meeting_exist["status"] == "active":
                multi_joins = disallow_join(room_id=mid, user_name=username)
                if multi_joins == "disallow":
                    return {"result": "User cannot join the same meeting twice."}
                try:
                    username_hash = oracle10.hash(username, user='isolveit')
                except TypeError:
                    return {"result": "Error occurred, please try again"}
                session["USERNAME"] = username_hash
                # session.permanent = True
                # _class_id combines meeting_id and stream_id
                _class_id = f"{meeting_exist['stream_id']}{mid}"
                user_info = f"{username}_{display_name}"
                return redirect(url_for("viewer", uid=user_info, _cid=_class_id)), 301

            if meeting_exist["status"] == "pending":
                # Ensures users access the meeting only when the host has started
                return {"result": "Meeting has not started."}
    return {"result": "Incorrect information."}


# Route for students to view lecture platform
@app.route('/meeting/v/<string:uid>/<string:_cid>')
@user_verification
def viewer(uid: str, _cid):
    stream_id, meeting_id = _cid[:5], _cid[5:]
    username, display_name = uid.split('_')
    try:
        check_username = oracle10.verify(uid, session.get("USERNAME"), user='isolveit')
        if check_username is False:
            return {"result": "Incorrect information."}

        return render_template('stream_pages/viewers.html', stream_id=stream_id,
                               room_id=meeting_id, user_id=username, user_name=display_name)
    except TypeError:
        return {"result": "Error occurred, please try again"}

# TODO: Route for student leaving meeting
