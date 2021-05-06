from random import sample
from string import ascii_letters
from datetime import datetime as dt
import requests


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
    converted_time = f"{'0'+hour_hand if int(hour_hand) < 10 else hour_hand}:{minute_hand}"
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


# Create broadcast on Ant Media Server
def create_broadcast(*, meeting_name, meeting_datetime):
    url = "http://localhost:5080/LiveApp/rest/v2/broadcasts/create"
    iso_date = meeting_datetime.date().isoformat()
    body = {
        "type": "liveStream",
        "name": meeting_name,
        "publish": True,
        "date": dt.fromisoformat(iso_date).timestamp(),
        "quality": "720p",
        "mp4Enabled": 1,
    }
    response = requests.post(url, json=body)
    data = response.json()
    return data["streamId"]

# TODO: Stop broadcast
