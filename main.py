import requests


url = "http://localhost:5080/LiveApp/rest/v2/broadcasts/006570276692345038048343"
# url = "http://localhost:5080/LiveApp/rest/v2/broadcasts/create"
# stop_url = "http://localhost:5080/LiveApp/rest/v2/broadcasts/006570276692345038048343/stop"
# body = {
#     "type": "liveStream",
#     "name": "PYTHON BROADCAST 2",
#     "publish": True,
#     "date": 1609637904.857858,
#     "quality": "1080p",
#     "mp4Enabled": 1,
# }
response = requests.delete(url)

# response = requests.get(url)
print(response.json())
# jj = response.json()
# print(jj['streamId'])
print(type(response.json()))

# sd = datetime.now().date().isoformat()
# datetime.fromisoformat(sd).timestamp()
# create start & end datetime = datetime(YYYY, MM, DD, HH, MM, SS)
# {'success': True, 'message': 'brodcast is deleted and stopped successfully', 'dataId': None, 'errorId': 0}
