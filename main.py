import requests


url = "http://localhost:5080/LiveApp/rest/v2/broadcasts/528009810085723443458930"
# url = "http://localhost:5080/LiveApp/rest/v2/broadcasts/create"
# body = {
#     "type": "liveStream",
#     "name": "PYTHON BROADCAST 2",
#     "publish": True,
#     "date": 1609637904.857858,
#     "quality": "1080p",
#     "mp4Enabled": 1,
# }
# response = requests.post(url, json=body)

response = requests.get(url)
print(response.json())
jj = response.json()
print(jj['streamId'])
print(type(response.json()))

# sd = datetime.now().date().isoformat()
# datetime.fromisoformat(sd).timestamp()
# create start & end datetime = datetime(YYYY, MM, DD, HH, MM, SS)
# {'streamId': '528009810085723443458930', 'status': 'finished', 'type': 'liveStream', 'name': 'PYTHON BROADCAST 3', 'description': 'Lets see', 'publish': True, 'date': 1609640181905, 'plannedStartDate': 0, 'plannedEndDate': 0, 'duration': 2164, 'endPointList': None, 'publicStream': True, 'is360': False, 'listenerHookURL': None, 'category': None, 'ipAddr': None, 'username': None, 'password': None, 'quality': '1080p', 'speed': 0.0, 'streamUrl': None, 'originAdress': '127.0.1.1', 'mp4Enabled': 1, 'webMEnabled': 0, 'expireDurationMS': 0, 'rtmpURL': 'rtmp://127.0.1.1/LiveApp/528009810085723443458930', 'zombi': False, 'pendingPacketSize': 0, 'hlsViewerCount': 0, 'webRTCViewerCount': 0, 'rtmpViewerCount': 0, 'startTime': 1609640236215, 'receivedBytes': 0, 'bitrate': 0, 'userAgent': 'N/A', 'latitude': None, 'longitude': None, 'altitude': None, 'mainTrackStreamId': None, 'subTrackStreamIds': None, 'absoluteStartTimeMs': 1609640236214, 'webRTCViewerLimit': -1, 'hlsViewerLimit': -1}
