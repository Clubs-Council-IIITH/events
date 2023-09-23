from os import getenv

from pymongo import MongoClient


# get mongodb URI and database name from environment variale
MONGO_URI = "mongodb://{}:{}@mongo:{}/".format(
    getenv("MONGO_USERNAME", default="username"),
    getenv("MONGO_PASSWORD", default="password"),
    getenv("MONGO_PORT", default="27107"),
)
MONGO_DATABASE = getenv("MONGO_DATABASE", default="default")

# instantiate mongo client
client = MongoClient(MONGO_URI)

# get database
db = client[MONGO_DATABASE]
eventsdb = db.events


# TEMPORARY script to update database with event codes
# docker exec -it <container_id> python3 -m db
if __name__ == "__main__":
    from utils import getEventCode

    events = eventsdb.find()
    codes = []
    for event in events:
        code = getEventCode(event["clubid"], event)
        codes.append(code)

        event["code"] = code
        eventsdb.update_one({"_id": event["_id"]}, {"$set": event})

    # assert uniqueness of event codes
    if len(set(codes)) != len(codes):
        print("Event codes not unique!")
        repeated = []
        for code in set(codes):
            if codes.count(code) > 1:
                repeated.append(code)
        print(repeated)
