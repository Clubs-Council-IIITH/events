import csv
from datetime import datetime
from os import getenv, makedirs

from pymongo import MongoClient

MONGO_URI = "mongodb://{}:{}@mongo:{}/".format(
    getenv("MONGO_USERNAME", default="username"),
    getenv("MONGO_PASSWORD", default="password"),
    getenv("MONGO_PORT", default="27107"),
)
MONGO_DATABASE = getenv("MONGO_DATABASE", default="default")
client = MongoClient(MONGO_URI)
db = client[MONGO_DATABASE]

makedirs("reports", exist_ok=True)

current_year = datetime.now().year
# Fetch active clubs
results = db.clubs.find({"state": "active"})
clubs = [result for result in results]
userlist = []

# Process each club
for club in clubs:
    if club["state"] != "active":
        continue
    results = db.members.find({"cid": club["cid"]})
    members = [result for result in results]
    for member in members:
        flag = 0
        for role in member["roles"]:
            if (
                role["end_year"] is None
                or int(role["end_year"]) >= current_year
            ):
                flag = 1
                break
        if flag == 1:
            users = db.users.find({"uid": member["uid"]})
            users = [user for user in users]
            for user in users:
                if user["img"] is None:
                    if user["uid"] not in userlist:
                        userlist.append(user["uid"])
                    break

# Write results to a CSV file
with open("reports/members_without_images.csv", "w", newline="") as csvfile:
    csvwriter = csv.writer(csvfile)

    # Write the header
    csvwriter.writerow(["User UID"])

    # Write the data
    for users in userlist:
        csvwriter.writerow([users])
