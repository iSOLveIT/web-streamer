import os
import re
from datetime import datetime as dt

from flask import redirect, render_template, request, url_for

from project import app, mongo
from project.sub_functions import random_str_generator, sec_to_time_format


os.environ['daily_limit'] = str(0)  # Daily Limit for number of scheduled meetings


# MAIN ROUTES
# Route for Homepage
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        full_name = request.form.get("fullname")
        m_topic = request.form.get("mTopic")
        m_date_time = f"{request.form.get('mDate')} {request.form.get('mTime')}"
        m_duration = (int(request.form.get("mHour", 1)) * 3600) + (int(request.form.get("mMinute", 0)) * 60)

        m_duration = sec_to_time_format(m_duration)
        if meeting_limit := int(os.environ.get('daily_limit')) > 30:
            return render_template('main_pages/index.html')
        os.environ["daily_limit"] = str(meeting_limit + 1)

        meeting_collection = mongo.get_collection("meetings")
        meeting_collection.insert_one({
            "meeting_id": random_str_generator(7),
            "room_id": random_str_generator(3),
            "instructor": full_name,
            "meeting_topic": m_topic,
            "meeting_date_time": m_date_time,
            "meeting_duration": m_duration,
            "OTP": random_str_generator(5),
            "student_records": {}
        })

        return f"{full_name, m_topic, m_date_time, m_duration}"
    return render_template('main_pages/index.html')


# HOST ROUTES
# Route for host authentication
@app.route('/host/authentication', methods=["GET", "POST"])
def host_auth():
    if request.method == "POST":
        otp = request.form.get("meeting_passcode")
        result = re.search(r"^[a-zA-Z0-9]{4}$", otp)
        if otp is None or result is None:
            return {"result": "Incorrect information."}
        meeting_collection = mongo.get_collection("meetings")
        meeting_details = meeting_collection.find_one({'otp': otp},
                                                      {'meeting_id': 1, 'room_id': 1})
        return redirect(url_for("studio", meeting_id=meeting_details['meeting_id'],
                                rid=meeting_details['room_id']))
    return render_template('main_pages/host_verify.html')


# Route for host to view broadcast studio
@app.route('/meeting/h/<string:meeting_id>/<string:rid>')
def studio(meeting_id, rid):
    return render_template('stream_pages/studio.html', stream_id=meeting_id, room_id=rid)


# STUDENTS (VIEWERS) ROUTE
# Route for joining meeting by students
@app.route('/join_meeting/<string:meet_params>', methods=["GET", "POST"])
def join_meeting(join_params):
    meeting_collection = mongo.get_collection("meetings")
    if join_params == "auto":
        meeting_id = request.args.get("mid")
        room_id = request.args.get("rid")

        check_meeting_id = re.search("^[a-zA-Z0-9]{7}$", meeting_id)
        check_room_id = re.search("^[a-zA-Z0-9]{3}$", room_id)

        if check_meeting_id is not None and check_room_id is not None:
            meeting_exist = meeting_collection.find_one({"meeting_id": meeting_id},
                                                        {"meeting_id": 1})
            if meeting_exist is None:
                return {'result': "Meeting has expired"}
        return redirect(url_for('user_attendance', rid=room_id, mid=meeting_id))
    if join_params == "details":
        if request.method == "POST":
            meeting_id = request.form.get("mid")
            room_id = request.form.get("rid")

            check_meeting_id = re.search("^[a-zA-Z0-9]{7}$", meeting_id)
            check_room_id = re.search("^[a-zA-Z0-9]{3}$", room_id)

            if check_meeting_id is not None and check_room_id is not None:
                meeting_exist = meeting_collection.find_one({"meeting_id": meeting_id},
                                                            {"meeting_id": 1})
                if meeting_exist is None:
                    return {'result': "Meeting has expired"}
                return redirect(url_for('user_attendance', rid=room_id, mid=meeting_id))
        return render_template('main_pages/join_meeting.html')


# Route for student details input
@app.route('/user/authentication/<string:rid>/<string:mid>', methods=["GET", "POST"])
def user_attendance(rid, mid):
    meeting_collection = mongo.get_collection("meetings")
    joined_at = dt.now().isoformat()
    left_at = dt.now().isoformat()

    if request.method == "POST":
        username = request.form.get("student_id", type=str)
        result = re.search(r"^10[0-9]{6}$", username)
        if username is None or result is None:
            return {"result": "Incorrect information."}

        meeting_data = meeting_collection.find_one({"meeting_id": mid}, {"OTP": 0})
        student_records = meeting_data['student_records']
        student_records.update([(username, [joined_at, left_at])])
        meeting_collection.find_one_and_update({"meeting_id": mid},
                                               {"$set": {"student_records": student_records}})
        return redirect(url_for("viewer", meeting_id=mid, rid=rid))

    return render_template('main_pages/user_verify.html')


# Route for students to view lecture platform
@app.route('/meeting/v/<string:meeting_id>/<string:rid>')
def viewer(meeting_id, rid):
    return render_template('stream_pages/viewers.html', stream_id=meeting_id, room_id=rid)
