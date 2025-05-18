from os import getenv
from datetime import datetime, timezone
from pymongo import MongoClient
import csv

current_year = datetime.now().year

# MongoDB connection
MONGO_URI = "mongodb://{}:{}@localhost:{}/".format(
    getenv("MONGO_USERNAME", default="username"),
    getenv("MONGO_PASSWORD", default="password"),
    getenv("MONGO_PORT", default="27017"),
)
MONGO_DATABASE = 'dev'
client = MongoClient(MONGO_URI)
db = client[MONGO_DATABASE]

# Fetch active clubs
results = db.clubs.find({"state": "active"})
clubs = [result for result in results]
userlist = []

# Process each club
for club in clubs:
    if club['state'] != "active":
        continue
    results = db.members.find({"cid": club['cid']})
    members = [result for result in results]
    for member in members:
        flag = 0
        for role in member['roles']:
            if role['end_year'] == None or int(role['end_year']) >= current_year:
                flag = 1
                break
        if flag == 1:
            users = db.users.find({"uid": member['uid']})
            users = [user for user in users]
            for user in users:
                if user['img'] == None:
                    if user['uid'] not in userlist:
                        userlist.append(user['uid'])
                    break

# Write results to a CSV file
with open("members_without_images.csv", "w", newline="") as csvfile:
    csvwriter = csv.writer(csvfile)

    # Write the header
    csvwriter.writerow(["User Name"])

    # Write the data
    for users in userlist:
        csvwriter.writerow([users])