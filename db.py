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
    MONGO_URI (str): MongoDB URI built from the above parameters.
    MONGO_DATABASE (str): MongoDB database name from environment variable.
                        Defaults to "default".
    client (pymongo.AsyncMongoClient): MongoDB client.
    db (pymongo.database.Database): MongoDB database.
    eventsdb (pymongo.collection.Collection): MongoDB collection for events.
    holidaysdb (pymongo.collection.Collection): MongoDB collection for
                                            holidays.
    event_reportsdb (pymongo.collection.Collection): MongoDB collection for
                                                event reports.
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


async def create_index() -> None:
    """
    Create MongoDB indexes for events-related collections
    if they don't already exist.

    This function creates the following indexes:

    - 'one_holiday_on_day': A unique index on the 'date' field in the holidays
        collection to ensure only one holiday can exist per day.

    - 'unique_event_code': A unique index on the 'code' field in the events
        collection to ensure event codes are unique.

    - 'unique_event_id': A unique index on the 'event_id' field in the
        event_reports collection to ensure there's only one report per event

    Returns:
        (None): This function does not return any value.
    """
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
        if "unique_event_id" not in (
            await event_reportsdb.index_information()
        ):
            await event_reportsdb.create_index(
                [("event_id", 1)], unique=True, name="unique_event_id"
            )
    except Exception:
        pass
