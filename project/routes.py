
import re
from datetime import datetime as dt
from datetime import timedelta
from functools import wraps

from flask import flash, redirect, render_template, request, session, url_for, abort
from flask_weasyprint import render_pdf
from passlib.hash import oracle10

from project import application, mongo, gh
from project.sub_functions import (contact_us_task, date_and_time, disallow_host, disallow_join,
                                   generate_meeting_details, random_str_generator, send_meeting_details_task)


# Check if host is verified
def host_verification(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'OTP' not in session:
            return redirect(url_for("all_verification", loader="host_verify")), 301
        return f(*args, **kwargs)

    return decorated


# Check if meeting_id exist and user is verified
def user_verification(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'USER_ID' not in session:
            return redirect(url_for("all_verification", loader="user_verify")), 301
        return f(*args, **kwargs)

    return decorated


# MAIN ROUTES
# Route for Homepage
@application.route('/', methods=['GET', 'POST'])
@application.route('/home', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        try:
            full_name = request.form.get("host_name")
            m_topic = request.form.get("mTopic")
            m_email = request.form.get("user_email", default="")
            optional_email = request.form.get("opt_email")
            # Class start date and time
            m_date = request.form.get('mDate')
            m_hour = request.form.get('hour_hand', type=int)
            m_minute = request.form.get('minute_hand', type=int)
            time_fmt = request.form.get('prompt')
            # Duration
            m_duration = request.form.get("mDuration")

            # Sanitize input received
            check_email = re.search(r"^[\w\-.]+?@(gmail|hotmail|yahoo|outlook).(com|org)$|^[\w\-.]+?@upsamail.edu.gh$", m_email)
            inputs_box = [check_email, re.search(r"^(\d{4})-(\d{2})-(\d{2})$", m_date),
                          m_hour, m_minute, re.search(r"(am|pm)", time_fmt), re.search(r"^[1-3]$", m_duration)]

            d_hour = int(m_duration)
            m_duration = timedelta(hours=d_hour).seconds

            if None in inputs_box or m_duration > 10800:
                flash(message="Please check your inputs and resubmit", category="danger")
                return render_template('app_index.html')

            m_date_time = date_and_time(_date=m_date, _time=f"{m_hour}:{m_minute}", _fmt=time_fmt)

            meeting_collection = mongo.get_collection("meetings")
            stream_id, meeting_id, otp = random_str_generator(5), random_str_generator(5), random_str_generator(4)

            prevent_idempotency = meeting_collection.find_one(
                {"$and": [
                    {"instructor": full_name},
                    {"meeting_start_dateTime": m_date_time},
                    {"host_ip": ip_address}
                ]},
                {"attendance_records": 0, "status": 0}
            )
            if prevent_idempotency:
                flash(message="Class scheduled already", category="normal")
                return render_template('app_index.html')

            meeting_collection.insert_one({
                "meeting_id": meeting_id,
                "stream_id": stream_id,
                "instructor": full_name,
                "meeting_email": m_email,
                "optional_email": optional_email,
                "meeting_topic": m_topic,
                "meeting_start_dateTime": m_date_time,
                "meeting_end_dateTime": m_date_time + timedelta(seconds=m_duration),
                "duration_left": m_duration,
                "OTP": otp,
                "host_ip": ip_address,
                "attendance_records": {},
                "status": "pending",
                "is_verified": False
            })
            recipients = [m_email if optional_email is None else m_email, optional_email]
            email_data = dict(user=full_name, recipient=recipients, topic=m_topic, meeting_id=meeting_id,
                              duration=m_duration, start_class=m_date_time.strftime('%A, %d %B, %Y %I:%M %p'), otp=otp)
            send_meeting_details_task.apply_async(args=[email_data])
            meeting_info = generate_meeting_details(meeting_data=email_data)
            flash(message="iSTREAM has emailed details of the scheduled class", category="success")
            return render_template('app_index.html', meeting_info=meeting_info)
        except (IndexError, ValueError):
            flash(message="Error occurred. Please try again", category="danger")
            return render_template('app_index.html')
    return render_template('app_index.html')


# HOST ROUTES
# Route for host authentication
@application.route('/host/authentication', methods=["POST"])
def host_auth():
    ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    multi_hosts = disallow_host(host_ip=ip_address)
    if multi_hosts == "disallow":
        flash(message="Another meeting by this Host is in progress", category="normal")
        return redirect(url_for("all_verification", loader="host_verify"))

    otp = request.form.get("meetingOTP")
    result = re.search(r"^[a-zA-Z0-9]{4}$", otp)    # Sanitize input
    if otp is None or result is None:
        flash(message="Please check input and try again", category="normal")
        return redirect(url_for("all_verification", loader="host_verify"))
    meeting_collection = mongo.get_collection("meetings")
    meeting_details = meeting_collection.find_one(
        {'OTP': otp},
        {'meeting_id': 1, 'stream_id': 1, 'is_verified': 1}
    )
    if meeting_details is not None and not meeting_details['is_verified']:
        try:
            otp_hash = oracle10.hash(otp, user='isolveit')
        except TypeError:
            flash(message="Error occurred, please try again", category="danger")
            return redirect(url_for("all_verification", loader="host_verify"))
        session["OTP"] = otp_hash
        session.modified = True
        session.permanent = True
        # _class_id combines meeting_id and stream_id
        _class_id = f"{meeting_details['stream_id']}{meeting_details['meeting_id']}"
        return redirect(url_for("studio", _cid=_class_id)), 301

    flash(message="Access Denied", category="danger")
    return redirect(url_for("all_verification", loader="host_verify"))


# Route for host to view broadcast studio
@application.route('/meeting/h/<string:_cid>')
@host_verification
def studio(_cid):
    ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    stream_id, meeting_id = _cid[:5], _cid[5:]
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find_one({'stream_id': stream_id},
                                               {'status': 1, 'is_verified': 1, 'OTP': 1, 'instructor': 1,
                                                'meeting_start_dateTime': 1, 'meeting_end_dateTime': 1,
                                                "meeting_topic": 1})
    # Calculate class end date and duration left
    meeting_start_date: dt = meeting_data['meeting_start_dateTime'].astimezone(tz=gh)
    meeting_end_date: dt = meeting_data['meeting_end_dateTime'].astimezone(tz=gh)
    seconds_left = (meeting_end_date - dt.now(tz=gh)).seconds
    check_otp = oracle10.verify(meeting_data['OTP'], session.get("OTP", ""), user='isolveit')
    permit_starting_class = [True if meeting_start_date <= dt.now(tz=gh) < meeting_end_date else False]

    # Check if meeting time is up and otp is verified before redirecting
    if permit_starting_class[0] and check_otp is True:
        meeting_topic = meeting_data["meeting_topic"]
        if meeting_data["status"] == "pending":
            # Update meeting status
            meeting_collection.find_one_and_update({"meeting_id": meeting_id},
                                                   {"$set": {"status": "active", "is_verified": True,
                                                             "host_ip": ip_address}})
            flash(message="Welcome to iSTREAM Studio. Kindly, allow access to camera and mic.", category="notice")
            return render_template('studio.html', stream_id=stream_id, room_id=meeting_id, seconds=seconds_left,
                                   meeting_topic=meeting_topic, user_id="Host", user_name=meeting_data['instructor'])
        # If meeting host has login and meeting has not expired and is not the meeting from the same computer
        if meeting_data["status"] == "active" and meeting_data['is_verified'] is True:
            flash(message="Welcome to iSTREAM Studio. Kindly, allow access to camera and mic.", category="notice")
            return render_template('studio.html', stream_id=stream_id, room_id=meeting_id, seconds=seconds_left,
                                   meeting_topic=meeting_topic, user_id="Host", user_name=meeting_data['instructor'])
        flash(message="Class has ended", category="normal")
        return redirect(url_for('all_verification', loader="host_verify"))
    flash(message="Access Denied", category="danger")
    return redirect(url_for('all_verification', loader="host_verify"))


# Route for searching and printing attendance report
@application.route('/search_attendance_report', methods=['GET', 'POST'])
def search_attendance_report():
    meeting_collection = mongo.get_collection("meetings")

    if request.method == "POST":
        search_term = request.form.get("search_term")
        result = re.search(r"^[a-zA-Z0-9]{4}$", search_term)    # Sanitize input
        if search_term is None or result is None:
            return render_template('attendance.html')
        meeting_data = meeting_collection.find_one({"$and": [{'OTP': search_term}, {'status': 'expired'}]},
                                                   {'meeting_topic': 1, 'meeting_start_dateTime': 1,
                                                    'meeting_end_dateTime': 1, 'meeting_id': 1})
        if meeting_data is None:
            return render_template('attendance.html')

        data = [meeting_data['meeting_topic'].upper(),
                meeting_data['meeting_start_dateTime'].strftime("%A, %d %B, %Y %I:%M %p"),
                meeting_data['meeting_end_dateTime'].strftime("%A, %d %B, %Y %I:%M %p"),
                meeting_data['meeting_id']]
        return render_template('attendance.html', results=data)
    return render_template('attendance.html')


# Route for host printing attendance report
@application.route('/attendance_report/<string:_mid>')
def attendance_report(_mid):
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find_one({"meeting_id": _mid}, {'status': 0, 'is_verified': 0,
                                                                      'meeting_email': 0, 'OTP': 0, 'host_ip': 0,
                                                                      'stream_id': 0, '_id': 0, 'meeting_duration': 0})
    attendance: dict = meeting_data["attendance_records"]
    meeting_details = [meeting_data["meeting_topic"].upper(), meeting_data["meeting_id"],
                       meeting_data["instructor"].title(),
                       meeting_data["meeting_start_dateTime"].strftime("%A, %d %B, %Y @ %I:%M %p"),
                       meeting_data['meeting_end_dateTime'].strftime("%A, %d %B, %Y @ %I:%M %p"), len(attendance)]
    return render_template('report.html', attendance=attendance.values(), m_details=meeting_details)


# Route to print attendance report
@application.route('/print_report/<string:_mid>_<string:_current>.pdf',
                   defaults={'_current': dt.now(tz=gh).strftime('%Y%m%d%H%M')})
def print_report_pdf(_mid, _current):
    # Make a PDF from another view using pdf generate task
    return render_pdf(url_for('attendance_report', _mid=_mid))


#  BOTH STUDENT AND HOST ROUTES
# Verify Host and Students
@application.route('/join_meeting/v/<string:loader>')
def all_verification(loader):
    result = re.search(r"^(host_verify|user_verify)$", loader)
    meeting_id = request.args.get('mid')
    if result is None:
        abort(404)
    if meeting_id is None:
        return render_template('verification.html', load=loader)
    return render_template('verification.html', load=loader, meeting_id=meeting_id)


# Route for contact us
@application.route('/contact_us', methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        u_name = request.form.get("c_name")
        u_email = request.form.get("c_email")
        u_subject = request.form.get("c_subj")
        u_msg = request.form.get("c_msg") 

        result = re.search(r"^[\w\-.]+?@(gmail|hotmail|yahoo|outlook).(com|org)$|^[\w\-.]+?@upsamail.edu.gh$", u_email)
        if None in [u_name, u_subject, u_msg, result]:
            flash(message="Message not sent. Please check your input and resubmit", category="danger")
            return redirect(url_for("contact"))
        email_data = dict(user=u_name, topic=u_subject, email=u_email, message=u_msg)
        contact_us_task.apply_async(args=[email_data], countdown=60)
        flash(message="Message sent", category="success")
        return redirect(url_for("contact")), 301
    return render_template('contact.html')


# STUDENTS (VIEWERS) ROUTE
# Route for student details input
@application.route('/user/authentication', methods=["POST"])
def user_attendance():
    meeting_id = request.form.get("mid")
    display_name = request.form.get("display_name", default="")
    user_id: str = request.form.get("user_id", default="")
    result = user_id.isdigit()

    # Sanitize input
    check_meeting_id = re.search(r"^[a-zA-Z0-9]{5}$", meeting_id)
    check_display_name = re.search(r"^[\w\d\-. ]{2,20}$", display_name)
    check_user_name = re.search(r"^10[0-9]{6}$", user_id)
    check_list = [check_meeting_id, check_user_name, check_display_name]

    if None not in check_list and result:
        meeting_collection = mongo.get_collection("meetings")
        meeting_exist = meeting_collection.find_one({"meeting_id": meeting_id}, {"stream_id": 1, "status": 1})
        if meeting_exist is not None:
            if meeting_exist["status"] == "active":
                multi_joins = disallow_join(room_id=meeting_id, user_id=user_id)
                if multi_joins == "disallow":
                    flash(message="User cannot join the same meeting twice", category="danger")
                    return redirect(url_for("all_verification", loader="user_verify"))
                try:
                    userid_hash = oracle10.hash(user_id, user='isolveit')
                except TypeError:
                    flash(message="Error occurred, please try again", category="danger")
                    return redirect(url_for("all_verification", loader="user_verify", mid=meeting_id))
                session["USER_ID"] = userid_hash
                session.modified = True
                session.permanent = True
                # _class_id combines meeting_id and stream_id
                _class_id = f"{meeting_exist['stream_id']}{meeting_id}"
                user_info = f"{user_id}_{display_name}"
                return redirect(url_for("viewer", uid=user_info, _cid=_class_id)), 301

            if meeting_exist["status"] == "pending":
                # Ensures users access the meeting only when the host has started
                flash(message="Meeting has not started.", category="normal")
                return redirect(url_for("all_verification", loader="user_verify", mid=meeting_id))
            flash(message="Class has ended", category="normal")
            return redirect(url_for("all_verification", loader="user_verify", mid=meeting_id))
    flash(message="Please ensure inputs entered are correct and resubmit", category="danger")
    return redirect(url_for("all_verification", loader="user_verify", mid=meeting_id))


# Route for students to view lecture platform
@application.route('/meeting/j/<string:uid>/<string:_cid>')
@user_verification
def viewer(uid: str, _cid):
    stream_id, meeting_id = _cid[:5], _cid[5:]
    user_id, display_name = uid.split('_')

    check_username = oracle10.verify(user_id, session.get("USER_ID", ""), user='isolveit')
    if check_username is False:
        flash(message="Incorrect user details. Please try again", category="normal")
        return redirect(url_for("all_verification", loader="user_verify", mid=meeting_id)), 301

    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find_one({"stream_id": stream_id},
                                               {"instructor": 1, "meeting_topic": 1,
                                                "meeting_end_dateTime": 1, "_id": 0})
    # Calculate duration left before meeting ends
    meeting_end_date: dt = meeting_data['meeting_end_dateTime'].astimezone(tz=gh)
    seconds_left = (meeting_end_date - dt.now(tz=gh)).seconds
    flash(message=f"Welcome {display_name} to the iSTREAM class.", category="notice")
    return render_template('viewer.html', stream_id=stream_id, room_id=meeting_id, seconds=seconds_left,
                           user_id=user_id, user_name=display_name, meeting_data=meeting_data)
