"""
script to fix the recent end timing being messed up for events older than 1 Feb
to run:
    docker exec -it services-events-1 /bin/bash
    export PYTHONPATH=`pwd`; python3 scripts/fix_end_times.py
"""


from db import eventsdb
from datetime import datetime, timedelta

fix = True

if __name__ == "__main__":
    events = eventsdb.find()
    for event in events:
        # Check if the difference between the start time and the end time is 2 minutes
        start_time1 = datetime.fromisoformat(event["datetimeperiod"][0].split("+")[0])
        end_time1 = datetime.fromisoformat(event["datetimeperiod"][1].split("+")[0])

        start_time = start_time1.replace(tzinfo=None)
        end_time = end_time1.replace(tzinfo=None)

        if (end_time - start_time) == timedelta(minutes=2):
            if fix:
                # If so, set the end time to be 1 hour after the start time
                end_time = start_time + timedelta(hours=2)

                event["datetimeperiod"][0] = start_time.isoformat() + "Z"
                event["datetimeperiod"][1] = end_time.isoformat() + "Z"

                print(event["datetimeperiod"])
                eventsdb.update_one({"_id": event["_id"]}, {"$set": event})
                
            print(f"Fixed end time for event {event['code']}")
