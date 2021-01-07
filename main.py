import requests
import json

# url = "http://localhost:5080/LiveApp/rest/v2/broadcasts/list/0/2/"
url = "http://localhost:5080/LiveApp/rest/v2/broadcasts/create"
body = {
    "type": "liveStream",
    "name": "PYTHON BROADCAST 3",
    "description": "Lets see",
    "publish": True,
    "date": 1609637904.857858,
    "plannedStartDate": 1609637904.857858,
    "plannedEndDate": 1609638024.857858,
    "quality": "1080p",
    "mp4Enabled": 1,
}
response = requests.post(url, json=body)

print(response.json())

# sd = datetime.now().date().isoformat()
# datetime.fromisoformat(sd).timestamp()
# create start & end datetime = datetime(YYYY, MM, DD, HH, MM, SS)
