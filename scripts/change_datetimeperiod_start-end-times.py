"""
script to migrate the datetimeperiod field in the events collection
to run:
    docker exec -it services-events-1 /bin/bash
    export PYTHONPATH=`pwd`; python3 scripts/change_datetimeperiod_start-end-times.py
"""


from db import eventsdb
from datetime import datetime
from utils import DATE_FORMAT

fix = True

if __name__ == "__main__":
    events = eventsdb.find()
    for event in events:
        # TODO: Replace datetimeperiod with start_time and end_time

        start_time = datetime.fromisoformat(event["datetimeperiod"][0].split("+")[0])
        end_time = datetime.fromisoformat(event["datetimeperiod"][1].split("+")[0])

        event["start_time"] = start_time.strftime(DATE_FORMAT)
        event["end_time"] = end_time.strftime(DATE_FORMAT)

        delta = end_time - start_time
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        event["duration"] = f"{hours:02}:{minutes:02}"

        # remove datetimeperiod
        del event["datetimeperiod"]

        eventsdb.update_one({"_id": event["_id"]}, {"$set": event})
