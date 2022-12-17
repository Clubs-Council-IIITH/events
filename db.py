from os import getenv

from pymongo import MongoClient


# get mongodb URI and database name from environment variale
MONGO_URI = getenv("MONGO_URI", default="mongodb://localhost:27017/")
MONGO_DB = getenv("MONGO_DB", default="default")

# instantiate mongo client
client = MongoClient(MONGO_URI)

# get database
db = client[MONGO_DB]
