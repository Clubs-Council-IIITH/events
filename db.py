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
holidaysdb = db.holidays

try:
    # check if the holidays index exists
    if "one_holiday_on_day" in holidaysdb.index_information():
        print("The holidays index exists.")
    else:
        # create the index
        holidaysdb.create_index(
            [("date", 1)], unique=True, name="one_holiday_on_day"
        )
        print("The holidays index was created.")

    print(holidaysdb.index_information())
except Exception:
    pass
