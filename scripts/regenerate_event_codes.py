"""
script to regenerate event codes for all events in the database
to run:
    docker-compose exec -it events /bin/bash
    export PYTHONPATH=`pwd`
    python3 scripts/regenerate_event_codes.py
"""

import fiscalyear

from db import eventsdb
from utils import getClubCode, FISCAL_START_MONTH

fiscalyear.START_MONTH = FISCAL_START_MONTH

def filter_set_by_prefix(input_set, prefix):
    return {item for item in input_set if item.startswith(prefix)}

if __name__ == "__main__":
    events = eventsdb.find().sort("datetimeperiod.0", 1)
    codes = set()
    for event in events:
        idx = 1
        club_code = getClubCode(event["clubid"])
        
        year = fiscalyear.FiscalDateTime.fromisoformat(
            event["datetimeperiod"][0].split("+")[0]
        ).fiscal_year
        year = str(year - 1)[-2:] + str(year)[-2:]

        filtered_codes = filter_set_by_prefix(codes, f"{club_code}{year}")
        idx = len(filtered_codes) + 1
        code = f"{club_code}{year}{idx:03d}"
        # while code in codes:
        #     if not code.startswith(f"{club_code}{year}"):
        #         continue
        #     idx += 1
        #     code = f"{club_code}{year}{idx:03d}"
        event["code"] = code
        eventsdb.update_one({"_id": event["_id"]}, {"$set": event})
        codes.add(code)
