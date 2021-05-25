from random import sample
from string import ascii_letters
from datetime import datetime as dt, timedelta
# import timeit
from project import mongo


# Combines date and time
def date_and_time(*, _date, _time, _fmt):
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
    converted_time = f"{'0' + hour_hand if int(hour_hand) < 10 else hour_hand}:{minute_hand}"
    if int(hour_hand) == 12 and _fmt == "am":
        converted_time = f"00:{minute_hand}"
    if (n_hour := int(hour_hand)) < 12 and _fmt == "pm":
        converted_time = f"{int(n_hour + 12)}:{minute_hand}"

    # combine the value for _date and value for converted _time to a datetime iso_format
    _iso_date_time = f"{_date}T{converted_time}"
    # create a datetime object using the datetime iso_format (_iso_date_time)
    _new_date_time = dt.fromisoformat(_iso_date_time)
    return _new_date_time


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


# Disconnect students if host disconnect
def disconnect_students(*, room_id):
    # Add user to attendance records in DB
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find_one({"meeting_id": room_id}, {"attendance_records": 1, "_id": 0})
    records: dict = meeting_data['attendance_records']
    if len(records) != 0:
        for r_key, r_value in records.items():
            r_value[1] = "left"
            records[f"{r_key}"] = r_value
        meeting_collection.find_one_and_update({"meeting_id": room_id},
                                               {"$set": {"attendance_records": records}})
    pass


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
                meeting_collection.find_one_and_update({"meeting_id": room_id},
                                                       {"$set": {"attendance_records": records}})
                return client_id
    # Add user if no record exist
    # user_records = [student_id, meeting_status, time_joined, time_left, name]
    user_data = [user_id, "joined", dt.now().isoformat(), dt.now().isoformat(), user_name]
    records.update([(client_id, user_data)])
    meeting_collection.find_one_and_update({"meeting_id": room_id},
                                           {"$set": {"attendance_records": records}})
    return client_id


# Disallow user from joining the same meeting twice
def disallow_join(*, room_id, user_name):
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find_one({"meeting_id": room_id}, {"attendance_records": 1, "_id": 0})
    records: dict = meeting_data['attendance_records']
    if len(records) != 0:
        for r_key, r_value in records.items():
            if r_value[0] == user_name and r_value[1] == "joined":
                # User record exist and user has joined meeting
                return "disallow"
    return "allow"


# Disallow the same host from hosting two meetings at once
def disallow_host(*, host_ip):
    meeting_collection = mongo.get_collection("meetings")
    meeting_data = meeting_collection.find({"host_ip": host_ip},
                                           {"status": 1, "meeting_start_dateTime": 1,
                                            "meeting_duration": 1, "_id": 0})
    check_status = [True for item in meeting_data if item['status'] == 'active' and dt.now() < (item['meeting_start_dateTime'] + timedelta(seconds=item['meeting_duration']))]
    if True in check_status:
        return "disallow"
    return "allow"


# if __name__ == '__main__':
#     import timeit
#     # s = f"create_broadcast(meeting_name={random_str_generator(3)})"
#     print(timeit.timeit(stmt="create_broadcast()", setup="from __main__ import create_broadcast",
#                         number=100))
