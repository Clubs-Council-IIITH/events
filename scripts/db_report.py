from os import getenv
from pymongo import MongoClient
from datetime import datetime, timezone
from db import db
# MongoDB connection
# MONGO_URI = "mongodb://{}:{}@localhost:{}/".format(
#     getenv("MONGO_USERNAME", default="username"),
#     getenv("MONGO_PASSWORD", default="password"),
#     getenv("MONGO_PORT", default="27017"),
# )
# MONGO_DATABASE='dev'

# Initialize variables
try:
    startYear = int(input("Enter the start year: "))
    endYear = int(input("Enter the end year: "))
except ValueError:
    print("Invalid input! Please enter valid integers for the years.")
    exit(1)
start_date = datetime(startYear, 4, 1, tzinfo=timezone.utc)
end_date = datetime(endYear, 3, 31, 23, 59, 59, tzinfo=timezone.utc)

results = db.clubs.find({"state": "active"})
clubs = [result for result in results]
club_events = {}
club_state = {}
club_budget = {}
approvals = 0
approval_time = 0
club_members_count = {}

# Process clubs and events
for club in clubs:
    if club['state'] != "active":
        continue

    results = db.events.find({"clubid": club['cid']})
    events = [result for result in results]

    club_events[club['name']] = [[], []]
    club_budget[club['name']] = [0, 0]

    for event in events:
        if event['status']['state'] != "approved":
            continue

        try:
            created_time = datetime.strptime(event['status']['submission_time'], "%d-%m-%Y %I:%M %p")
            last_updated_time = datetime.strptime(event['status']['last_updated_time'], "%d-%m-%Y %I:%M %p")
            created_time = created_time.replace(tzinfo=timezone.utc)
            last_updated_time = last_updated_time.replace(tzinfo=timezone.utc)
            time_difference = last_updated_time - created_time
            approvals += 1
            approval_time += time_difference.total_seconds()
        except:
            pass

        event_start = datetime.fromisoformat(event['datetimeperiod'][0].replace("Z", "+00:00"))
        event_end = datetime.fromisoformat(event['datetimeperiod'][1].replace("Z", "+00:00"))

        if start_date <= event_start <= end_date:
            if 'internal' in event['audience']:
                club_events[club['name']][0].append(event)
            else:
                club_events[club['name']][1].append(event)
            if club['category'] in ["cultural", "technical", "affinity"]:
                for budget in event['budget']:
                    club_budget[club['name']][0] += budget['amount']
                    club_budget[club['name']][1] += 1

    if club['category'] in ["cultural", "technical", "affinity"]:
        if club_budget[club['name']][1] > 0:
            club_budget[club['name']][0] /= club_budget[club['name']][1]
        
    total_events = len(club_events[club['name']][0]) + len(club_events[club['name']][1])
    club_state[club['name']] = "active" if total_events >= 4 else "inactive"

    results = db.members.find({"cid": club['cid']})
    members = [result for result in results]
    club_members_count[club['name']] = [0, 0, 0, 0]
    for member in members:
        for role in member['roles']:
            if role['start_year'] and int(role['start_year']) == startYear:
                club_members_count[club['name']][0] += 1
            if role['end_year'] and int(role['end_year']) == startYear:
                club_members_count[club['name']][1] += 1
            if role['end_year'] and int(role['end_year']) > startYear:
                club_members_count[club['name']][2] += 1
                club_members_count[club['name']][3] += int(role['end_year']) - startYear

    if club_members_count[club['name']][2] > 0:
        club_members_count[club['name']][3] /= club_members_count[club['name']][2]
        club_members_count[club['name']][3] = round(club_members_count[club['name']][3], 2)

# Write results to a text file
with open("database_report.txt", "w") as file:
    file.write(f"Database Report from {startYear} to {endYear}\n")
    file.write(f"Generated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n")
    file.write("\n\nClub Events:\n")
    for club_name, events in club_events.items():
        file.write(f"\n{club_name}\n")
        file.write(f"   |~Internal Events: {len(events[0])}\n")
        file.write(f"   |~Non-Internal Events: {len(events[1])}\n")
        
    file.write("\n\n")
    
    file.write("Inactive Clubs/Bodies:\n")
    for club_name, state in club_state.items():
        if state == "inactive":
            file.write(f"{club_name}\n")

    file.write("\n\n")
    
    file.write("\nClub Budgets:\n")
    for club_name, budget in club_budget.items():
        file.write(f"{club_name}, Average Budget: {budget[0]}\n")

    file.write("\n\n")
    
    file.write("\nClub Members Count:\n")
    for club_name, counts in club_members_count.items():
        file.write(f"{club_name}\n   |~Members joined this year: {counts[0]}\n   |~Members left this year: {counts[1]}"
                   f"\n   |~Active Members: {counts[2]}\n   |~Avg Active Membership Duration: {counts[3]}\n")

    if approvals > 0:
        avg_approval_days = round((approval_time/3600)/24,2)
        file.write(f"\nAverage Approval Time (days): {avg_approval_days}\n")
    else:
        file.write("\nNo approvals found in the given date range.\n")