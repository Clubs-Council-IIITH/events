"""
MongoDB Initialization Module

This module sets up a connection to a MongoDB database and ensures that the required indexes are created.
This module connects to the MongoDB database using environment variables for authentication.
Ensures that a 'one_holiday_on_day' index is present on the `date` field in the Events collection.
It specifically exports the events collection of the database.

Environment Variables:
    `MONGO_USERNAME` (str): MongoDB username. Defaults to "username".
    `MONGO_PASSWORD` (str): MongoDB password. Defaults to "password".
    `MONGO_PORT` (str): MongoDB port. Defaults to "27017".
    `MONGO_DATABASE` (str): MongoDB database name. Defaults to "default".

"""

from os import getenv

from pymongo import MongoClient

# get mongodb URI and database name from environment variable
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
holidaysdb = db.holidays

try:
    # check if the holidays index exists
    if "one_holiday_on_day" not in holidaysdb.index_information():
        # create the index
        holidaysdb.create_index(
            [("date", 1)], unique=True, name="one_holiday_on_day"
        )
except Exception:
    pass
