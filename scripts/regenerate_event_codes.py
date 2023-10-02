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


if __name__ == "__main__":
    events = eventsdb.find()
    codes = set()
    for event in events:
        idx = 1
        club_code = getClubCode(event["clubid"])
        year = fiscalyear.FiscalDateTime.fromisoformat(
            event["datetimeperiod"][0].split("+")[0]
        ).fiscal_year
        code = f"{club_code}{year}{idx:03d}"
        while code in codes:
            idx += 1
            code = f"{club_code}{year}{idx:03d}"
        event["code"] = code
        eventsdb.update_one({"_id": event["_id"]}, {"$set": event})
        codes.add(code)
