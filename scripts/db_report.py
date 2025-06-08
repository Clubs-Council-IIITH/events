import csv
from datetime import datetime, timezone
from os import getenv, makedirs

import matplotlib.pyplot as plt
from pymongo import MongoClient

# MongoDB connection
MONGO_URI = "mongodb://{}:{}@mongo:{}/".format(
    getenv("MONGO_USERNAME", default="username"),
    getenv("MONGO_PASSWORD", default="password"),
    getenv("MONGO_PORT", default="27107"),
)
MONGO_DATABASE = getenv("MONGO_DATABASE", default="default")
client = MongoClient(MONGO_URI)
db = client[MONGO_DATABASE]

try:
    startYear = int(input("Enter the start year: "))
    endYear = int(input("Enter the end year: "))
    deadclub_threshold = int(
        input("Enter the dead club threshold (default 4): ") or 4
    )
except:  # noqa: E722
    print("Invalid input! Please enter valid integers for the years.")
    exit(1)
if startYear > endYear:
    print("Start year cannot be greater than end year.")
    exit(1)
if deadclub_threshold < 0:
    print("Dead club threshold cannot be negative.")
    exit(1)

include_bodies = (
    input("Do you want to include bodies in the report? (yes/no): ")
    .strip()
    .lower()
    .startswith("y")
)
club_categories = ["cultural", "technical", "affinity", "other"]
if include_bodies:
    club_categories.append("body")


start_date = datetime(startYear, 4, 1, tzinfo=timezone.utc)
end_date = datetime(endYear, 3, 31, 23, 59, 59, tzinfo=timezone.utc)

clubs = list(
    db.clubs.find(
        {
            "state": "active",
            "category": {"$in": club_categories},
        },
        {"_id": 0, "cid": 1, "name": 1, "state": 1},
    )
)
club_events = {}
club_state = {}
club_budget = {}
approvals = 0
approval_time_sum = 0
club_members_count = {}

for club in clubs:
    events = list(db.events.find({"clubid": club["cid"]}))

    club_events[club["name"]] = [[], [], 0]
    club_budget[club["name"]] = [0, 0]

    exception_count = 0

    for event in events:
        if event["status"]["state"] == "approved":
            event_start = datetime.fromisoformat(
                event["datetimeperiod"][0].replace("Z", "+00:00")
            )
            event_end = datetime.fromisoformat(
                event["datetimeperiod"][1].replace("Z", "+00:00")
            )

            if start_date <= event_start <= end_date:
                try:
                    cc_approver_time = event["status"].get("cc_approver_time")
                    slo_approver_time = event["status"].get(
                        "slo_approver_time"
                    )
                    slc_approver_time = event["status"].get(
                        "slc_approver_time"
                    )
                    approver_times = []
                    if cc_approver_time and cc_approver_time != "Not Approved":
                        approver_times.append(
                            datetime.strptime(
                                cc_approver_time, "%d-%m-%Y %I:%M %p"
                            ).replace(tzinfo=timezone.utc)
                        )
                    if (
                        slo_approver_time
                        and slo_approver_time != "Not Approved"
                    ):
                        approver_times.append(
                            datetime.strptime(
                                slo_approver_time, "%d-%m-%Y %I:%M %p"
                            ).replace(tzinfo=timezone.utc)
                        )
                    if (
                        slc_approver_time
                        and slc_approver_time != "Not Approved"
                    ):
                        approver_times.append(
                            datetime.strptime(
                                slc_approver_time, "%d-%m-%Y %I:%M %p"
                            ).replace(tzinfo=timezone.utc)
                        )

                    if approver_times:
                        approval_time = max(approver_times)
                        approval_time = approval_time.replace(
                            tzinfo=timezone.utc
                        )
                        created_time = datetime.strptime(
                            event["status"]["submission_time"],
                            "%d-%m-%Y %I:%M %p",
                        )
                        created_time = created_time.replace(
                            tzinfo=timezone.utc
                        )
                        approval_time = approval_time.replace(
                            tzinfo=timezone.utc
                        )
                        time_difference = approval_time - created_time
                        approvals += 1
                        approval_time_sum += time_difference.total_seconds()
                except:  # noqa: E722
                    exception_count += 1
                if "internal" in event["audience"]:
                    club_events[club["name"]][0].append(event)
                else:
                    club_events[club["name"]][1].append(event)
                for budget in event["budget"]:
                    club_budget[club["name"]][0] += budget["amount"]
                    club_budget[club["name"]][1] += 1

    if exception_count > 0:
        print(
            "Exception occurred while processing events for club '{}'. "
            "Number of exceptions: {}".format(club["name"], exception_count)
        )

    if club_budget[club["name"]][1] > 0:
        club_budget[club["name"]][1] = (
            club_budget[club["name"]][0] / club_budget[club["name"]][1]
        )

    club_events[club["name"]][2] = len(club_events[club["name"]][0]) + len(
        club_events[club["name"]][1]
    )
    club_state[club["name"]] = club["state"]

    members = list(db.members.find({"cid": club["cid"]}))
    club_members_count[club["name"]] = [0, 0, 0, 0]
    for member in members:
        for role in member["roles"]:
            if role["start_year"] and int(role["start_year"]) == startYear:
                club_members_count[club["name"]][0] += 1
            if role["end_year"] and int(role["end_year"]) == startYear:
                club_members_count[club["name"]][1] += 1
            if role["end_year"] and int(role["end_year"]) > startYear:
                club_members_count[club["name"]][2] += 1
                club_members_count[club["name"]][3] += (
                    int(role["end_year"]) - startYear
                )

    if club_members_count[club["name"]][2] > 0:
        club_members_count[club["name"]][3] /= club_members_count[
            club["name"]
        ][2]
        club_members_count[club["name"]][3] = round(
            club_members_count[club["name"]][3], 2
        )

makedirs("reports", exist_ok=True)
with open("reports/database_report.csv", "w", newline="") as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(
        [
            "Database Report from {} to {}".format(
                start_date.strftime("%d-%m-%Y"), end_date.strftime("%d-%m-%Y")
            )
        ]
    )
    csvwriter.writerow([f"Active Clubs (>={deadclub_threshold} events)"])
    csvwriter.writerow(
        [
            "Club Name",
            "State",
            "Internal Events",
            "Non-Internal Events",
            "Total no of Events",
            "Total Budget",
            "Average Budget",
            "Members Joined in this Period",
            "Members Left in this Period",
            "Active Members",
            "Avg Membership Duration",
        ]
    )

    for club_name in sorted(club_events.keys()):
        internal_events = len(club_events[club_name][0])
        non_internal_events = len(club_events[club_name][1])
        total_events = club_events[club_name][2]
        total_budget = club_budget[club_name][0]
        avg_budget = club_budget[club_name][1]
        members_joined = club_members_count[club_name][0]
        members_left = club_members_count[club_name][1]
        active_members = club_members_count[club_name][2]
        avg_membership_duration = club_members_count[club_name][3]
        state = club_state[club_name]

        if total_events >= deadclub_threshold:
            csvwriter.writerow(
                [
                    club_name,
                    state,
                    internal_events,
                    non_internal_events,
                    total_events,
                    total_budget,
                    avg_budget,
                    members_joined,
                    members_left,
                    active_members,
                    avg_membership_duration,
                ]
            )
    csvwriter.writerow([])
    key = 0
    csvwriter.writerow([f"Dead Clubs (<{deadclub_threshold} events)"])
    csvwriter.writerow(
        [
            "Club Name",
            "Internal Events",
            "Non-Internal Events",
            "Total no of Events",
            "Total Budget",
            "Average Budget",
            "Members Joined in this Period",
            "Members Left in this Period",
            "Active Members",
            "Avg Membership Duration",
        ]
    )

    for club_name in sorted(club_events.keys()):
        internal_events = len(club_events[club_name][0])
        non_internal_events = len(club_events[club_name][1])
        total_events = club_events[club_name][2]
        total_budget = club_budget[club_name][0]
        avg_budget = club_budget[club_name][1]
        members_joined = club_members_count[club_name][0]
        members_left = club_members_count[club_name][1]
        active_members = club_members_count[club_name][2]
        avg_membership_duration = club_members_count[club_name][3]
        state = club_state[club_name]
        if total_events < deadclub_threshold:
            csvwriter.writerow(
                [
                    club_name,
                    internal_events,
                    non_internal_events,
                    total_events,
                    total_budget,
                    avg_budget,
                    members_joined,
                    members_left,
                    active_members,
                    avg_membership_duration,
                ]
            )
            key += 1
    csvwriter.writerow(["Total no of dead clubs", key])
    csvwriter.writerow([])
    if approvals > 0:
        avg_approval_days = (
            round((approval_time_sum / 3600) / 24, 2)
        ) / approvals
        csvwriter.writerow(["Total Approvals", approvals])
        csvwriter.writerow(["Average Approval Time (days)", avg_approval_days])
    else:
        csvwriter.writerow(["No approvals found in the given date range."])

# raindrop plot of approval times
all_events = db.events.find({"status.state": "approved"})
filtered_events = [
    event
    for event in all_events
    if "submission_time" in event["status"]
    and event["status"]["submission_time"] is not None
]
# sort by submission time
sorted_events = sorted(
    filtered_events,
    key=lambda event: datetime.strptime(
        event["status"]["submission_time"], "%d-%m-%Y %I:%M %p"
    ),
)

approval_times = []
exception_count = 0
for event in sorted_events:
    try:
        created_time = datetime.strptime(
            event["status"]["submission_time"], "%d-%m-%Y %I:%M %p"
        )
        created_time = created_time.replace(tzinfo=timezone.utc)
        cc_approver_time = event["status"].get("cc_approver_time")
        slo_approver_time = event["status"].get("slo_approver_time")
        slc_approver_time = event["status"].get("slc_approver_time")
        approver_times = []
        if cc_approver_time and cc_approver_time != "Not Approved":
            approver_times.append(
                datetime.strptime(
                    cc_approver_time, "%d-%m-%Y %I:%M %p"
                ).replace(tzinfo=timezone.utc)
            )
        if slo_approver_time and slo_approver_time != "Not Approved":
            approver_times.append(
                datetime.strptime(
                    slo_approver_time, "%d-%m-%Y %I:%M %p"
                ).replace(tzinfo=timezone.utc)
            )
        if slc_approver_time and slc_approver_time != "Not Approved":
            approver_times.append(
                datetime.strptime(
                    slc_approver_time, "%d-%m-%Y %I:%M %p"
                ).replace(tzinfo=timezone.utc)
            )

        if approver_times:
            approval_time = max(approver_times)
            approval_time = approval_time.replace(tzinfo=timezone.utc)
            time_difference = approval_time - created_time
            approval_times.append(
                time_difference.total_seconds() / (3600 * 24)
            )
    except:  # noqa: E722
        exception_count += 1
if exception_count > 0:
    print(
        "Exception occurred while processing approval times. "
        "Number of exceptions: {}".format(exception_count)
    )

if len(approval_times) > 0:
    # Raindrop plot
    plt.figure(figsize=(10, 6))
    plt.scatter(
        range(len(approval_times)), approval_times, alpha=0.6, color="blue"
    )
    plt.title(
        f"Raindrop Plot of Approval Times for {len(approval_times)} Events"
    )
    plt.xlabel("Event Index (Sorted by Submission Time)")
    plt.ylabel("Approval Time (days)")
    plt.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig("reports/approval_times_plot.png")
else:
    print("No approval times found in the given date range for raindrop plot.")
