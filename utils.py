import requests
import fiscalyear
from datetime import datetime, timedelta

from db import eventsdb

# start month of financial year
fiscalyear.START_MONTH = 7


def getClubs(cookies=None):
    """
    Function to call the all clubs query
    """
    try:
        query = """
                    query AllClubs {
                        allClubs {
                            cid
                            name
                            code
                        }
                    }
                """
        if cookies:
            request = requests.post(
                "http://gateway/graphql",
                json={"query": query},
                cookies=cookies,
            )
        else:
            request = requests.post("http://gateway/graphql", json={"query": query})
        return request.json()["data"]["allClubs"]
    except:
        return []


# get club code from club id
def getClubCode(clubid: str) -> str | None:
    allclubs = getClubs()
    for club in allclubs:
        if club["cid"] == clubid:
            return club["code"]
    return None


# generate event code based on time and club
def getEventCode(clubid, event=None):
    club_code = getClubCode(clubid)
    if event:
        year = fiscalyear.FiscalDateTime.fromisoformat(
            event["datetimeperiod"][0].split("+")[0]  # remove timezone because UTC
        ).fiscal_year
    else:
        year = fiscalyear.FiscalYear.current().fiscal_year

    # fetch all events of the club from the last 2 years
    if not event:
        club_events = eventsdb.find(
            {
                "clubid": clubid,
                "datetimeperiod": {
                    "$gte": (datetime.now() - timedelta(days=2 * 365)).isoformat()
                },
            }
        )
    else:
        club_events = eventsdb.find(
            {
                "_id": {"$ne": event["_id"]},
                "clubid": clubid,
                "datetimeperiod": {
                    "$gte": (datetime.now() - timedelta(days=2 * 365)).isoformat(),
                    "$lte": event["datetimeperiod"][0],
                },
            }
        )

    # get count of events in the current fiscal year
    event_count = 0
    for event in club_events:
        if (
            fiscalyear.FiscalDateTime.fromisoformat(
                event["datetimeperiod"][0].split("+")[0]  # remove timezone because UTC
            ).fiscal_year
            == year
        ):
            event_count += 1
    event_count += 1

    if club_code is None:
        raise ValueError("Invalid clubid")

    return f"{club_code}{year}{event_count:03d}"  # format: CODE20XX00Y
