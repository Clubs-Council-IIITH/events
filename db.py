"""
MongoDB Initialization Module.

This module sets up the connection to the MongoDB database.
It ensures that the required indexes are created.

Attributes:
    MONGO_USERNAME (str): An environment variable having MongoDB
                          username. Defaults to "username".
    MONGO_PASSWORD (str): An environment variable having MongoDB password.
                          Defaults to "password".
    MONGO_PORT (str): MongoDB port. Defaults to "27017".
    MONGO_URI (str): MongoDB URI.
    MONGO_DATABASE (str): MongoDB database name.
    client (MongoClient): MongoDB client.
    db (Database): MongoDB database.
    eventsdb (Collection): MongoDB collection for events.
    holidaysdb (Collection): MongoDB collection for holidays.
    event_reportsdb (Collection): MongoDB collection for event reports.
"""

from os import getenv

from pymongo import AsyncMongoClient

# get mongodb URI and database name from environment variable
MONGO_URI = "mongodb://{}:{}@mongo:{}/".format(
    getenv("MONGO_USERNAME", default="username"),
    getenv("MONGO_PASSWORD", default="password"),
    getenv("MONGO_PORT", default="27107"),
)
MONGO_DATABASE = getenv("MONGO_DATABASE", default="default")

# instantiate mongo client
client = AsyncMongoClient(MONGO_URI)

# get database
db = client[MONGO_DATABASE]
eventsdb = db.events
holidaysdb = db.holidays
event_reportsdb = db.event_reports
async def create_index():
    try:
        # check if the holidays index exists
        if "one_holiday_on_day" not in (await holidaysdb.index_information()):
            # create the index
            await holidaysdb.create_index(
                [("date", 1)], unique=True, name="one_holiday_on_day"
            )
        if "unique_event_code" not in (await eventsdb.index_information()):
            await eventsdb.create_index(
                [("code", 1)], unique=True, name="unique_event_code"
            )
        if "unique_event_id" not in (await event_reportsdb.index_information()):
            await event_reportsdb.create_index(
                [("event_id", 1)], unique=True, name="unique_event_id"
            )
    except Exception:
        pass
