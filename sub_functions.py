from datetime import datetime as dt
from random import sample
from string import ascii_letters

from flask_mail import Message
from pymongo import ReturnDocument

from project import application, celery, mail, mongo, gh


# Combines date and time
def date_and_time(*, _date, _time, _fmt) -> dt:
    """
    The function performs the ff.:
        - convert _time from 12 hour to 24 hour based on value for format
        - combine the value for _date and value for converted _time to a datetime iso_format
        - create a datetime object using the datetime iso_format
    :param _date: a string value of date in the format YYYY-MM-dd
    :param _time: a string value of time from 1:00 to 12:00
    :param _fmt: am or pm format
    :return: datetime object
    """
    # convert _time from 12 hour to 24 hour based on value for format
    hour_hand, minute_hand = _time.split(":")
    converted_time = f"{hour_hand}:{minute_hand}"
    if int(hour_hand) == 12 and _fmt == "am":
        converted_time = f"0:{minute_hand}"
    if (n_hour := int(hour_hand)) < 12 and _fmt == "pm":
        converted_time = f"{int(n_hour + 12)}:{minute_hand}"

    year, month, day = _date.split("-", maxsplit=3)
    hour, minute = converted_time.split(":", maxsplit=1)

    # create new datetime object
    new_date_time = dt(year=int(year), month=int(month), day=int(day),
                       hour=int(hour), minute=int(minute), tzinfo=gh)

    return new_date_time


# Convert seconds to hours and minutes
def sec_to_time_format(total_secs=0):
    # Separate seconds into hours, and minutes
    hours = (total_secs % 86400) // 3600
    return hours


# Random string generator
def random_str_generator(str_length):
    alphanum = ascii_letters + '0123456789'
    output = ''.join(sample(alphanum, str_length))
    return output


# Generate meeting details string
def generate_meeting_details(*, meeting_data):
    msg = f'''{meeting_data['user']} is inviting you to a scheduled iSTREAM class.

Class Details:
    - Instructor: {meeting_data['user']}
    - Topic: {meeting_data['topic']}
    - Scheduled Start Date and Time: {meeting_data['start_class']} GMT
    - Duration: {sec_to_time_format(meeting_data['duration'])} hour(s)
    - Class ID: {meeting_data['meeting_id']}
    - Join iSTREAM Class: http://127.0.0.1:17000/join_meeting/v/user_verify?mid={meeting_data['meeting_id']}

NOTE: We emailed access code for starting class (Class OTP) to the email address provided.
Thank you.
'''
    return msg


# Disconnect students if host disconnect
def disconnect_students(*, room_id):
    # Add user to attendance records in DB
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find_one({"meeting_id": room_id}, {"attendance_records": 1, "_id": 0})
    records: dict = meeting_data['attendance_records']

    if len(records) != 0:
        for r_key, r_value in records.items():
            if r_value[1] == "joined":
                r_value[1] = "left"
                r_value[3] = dt.now(tz=gh).strftime("%Y-%m-%d %H:%M")
                records[f"{r_key}"] = r_value
        meeting_collection.find_one_and_update({"meeting_id": room_id},
                                               {"$set": {"attendance_records": records}})


# User management meeting
def user_management(*, client_id, room_id, user_name, user_id):
    # Purpose of function: For adding users or updating user details in case of a rejoin
    # Reasons for rejoin: User left but meeting is in progress or
    # Host ended meeting by mistake, this means users will rejoin
    # This means there is data about user already so we have to change the client id for socket_io
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find_one({"meeting_id": room_id}, {"attendance_records": 1, "_id": 0})
    records: dict = meeting_data['attendance_records']

    if records != 0:
        for r_key, r_value in records.items():
            if r_value[0] == user_id:
                # If user record exist, update client_id (key)
                user_data = records.pop(f"{r_key}")  # Remove old data
                user_data[1] = "joined"
                user_data[4] = user_name
                records.update([(client_id, user_data)])  # Update user record with new client_id as key
                members = meeting_collection.find_one_and_update({"meeting_id": room_id},
                                                                 {"$set": {"attendance_records": records}},
                                                                 projection={'attendance_records': 1, '_id': 0},
                                                                 return_document=ReturnDocument.AFTER)

                return [user[0] for user in members['attendance_records'].values() if user[1] == "joined"]
    # Add user if no record exist
    # user_records = [user_id, meeting_status, time_joined, time_left, name]
    user_data = [user_id, "joined", dt.now(tz=gh).strftime("%Y-%m-%d %H:%M"),
                 dt.now(tz=gh).strftime("%Y-%m-%d %H:%M"), user_name]
    records.update([(client_id, user_data)])
    members = meeting_collection.find_one_and_update({"meeting_id": room_id},
                                                     {"$set": {"attendance_records": records}},
                                                     projection={'attendance_records': 1, '_id': 0},
                                                     return_document=ReturnDocument.AFTER)
    return [user[0] for user in members['attendance_records'].values() if user[1] == "joined"]


# Disallow user from joining the same meeting twice
def disallow_join(*, room_id, user_id):
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find_one({"meeting_id": room_id}, {"attendance_records": 1, "_id": 0})
    records: dict = meeting_data['attendance_records']
    if len(records) != 0:
        for r_key, r_value in records.items():
            if r_value[0] == user_id and r_value[1] == "joined":
                # User record exist and user has joined meeting
                return "disallow"
    return "allow"


# Disallow the same host from hosting two meetings at once
def disallow_host(*, host_ip):
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find({"host_ip": host_ip},
                                           {"status": 1, "meeting_end_dateTime": 1, "_id": 0})

    check_status = [True for item in meeting_data if item['status'] == 'active' and
                    dt.now(tz=gh) < item['meeting_end_dateTime'].astimezone(tz=gh)]
    if True in check_status:
        return "disallow"
    return "allow"


# Send meeting details to Host
@celery.task
def send_meeting_details_task(email_data):
    msg = Message("Scheduled Class Details", sender=("iSTREAM", "isolveitgroup@gmail.com"),
                  recipients=email_data['recipient'])
    msg.body = f'''{email_data['user']} is inviting you to a scheduled iSTREAM class.

Class Details:
        - Instructor: {email_data['user']}
        - Topic: {email_data['topic']}
        - Scheduled Start Date and Time: {email_data['start_class']} GMT
        - Duration: {sec_to_time_format(email_data['duration'])} hour(s)
        - Class ID: {email_data['meeting_id']}
        - Join iSTREAM Class: http://127.0.0.1:17000/join_meeting/v/user_verify?mid={email_data['meeting_id']}

NB: Please don't share your meeting OTP (One-Time Password) with anyone.
Class OTP: {email_data['otp']}

Best Regards,
iSTREAM
'''
    with application.app_context():
        mail.send(msg)


# Send contact information to iSTREAM
@celery.task
def contact_us_task(email_data):
    msg = Message(email_data['topic'], sender=("iSTREAM", "isolveitgroup@gmail.com"),
                  recipients=["isolveitgroup@gmail.com"])
    msg.body = f'''Hello iSTREAM,
{email_data['message']}
Best Regards,
{email_data['user'].title()}

Sender's Email: {email_data['email']}
Sent at: {dt.now(tz=gh).strftime("%A, %d %B, %Y %I:%M %p")} GMT
'''
    with application.app_context():
        mail.send(msg)
