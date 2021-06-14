from datetime import datetime as dt
from zoneinfo import ZoneInfo

from pymongo import MongoClient


# Mongo Config
mongo_client = MongoClient(host="localhost", port=18000)
mongo_db = mongo_client.get_database("vCLASS")
mongo_col = mongo_db.get_collection("meetings")

current = dt.now(tz=ZoneInfo("GMT"))
mongo_col.update_many({"meeting_end_dateTime": {"$lt": current.now()}}, {"$set": {"duration_left": 0, "status": "expired", "is_verified": True}})
