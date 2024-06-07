import os
from datetime import datetime
from typing import List

import fiscalyear
import pytz
import requests

from db import eventsdb

inter_communication_secret = os.getenv("INTER_COMMUNICATION_SECRET")

# start month of financial year
FISCAL_START_MONTH = 4

# fiscalyear config
fiscalyear.START_MONTH = FISCAL_START_MONTH


def getMember(cid, uid, cookies=None):
    """
    Function to call the member query
    """
    try:
        query = """
            query Member($memberInput: SimpleMemberInput!) {
              member(memberInput: $memberInput) {
                _id
                cid
                poc
                uid
              }
            }
        """
        variables = {"memberInput": {"cid": cid, "uid": uid, "rid": None}}
        if cookies:
            request = requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variables},
                cookies=cookies,
            )
        else:
            request = requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variables},
            )
        return request.json()["data"]["member"]

    except Exception:
        return None


def getUser(uid, cookies=None):
    """
    Function to get a particular user details
    """
    try:
        query = """
            query GetUserProfile($userInput: UserInput!) {
                userProfile(userInput: $userInput) {
                    firstName
                    lastName
                    email
                    rollno
                }
                userMeta(userInput: $userInput) {
                    phone
                }
            }
        """
        variable = {"userInput": {"uid": uid}}
        if cookies:
            request = requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variable},
                cookies=cookies,
            )
        else:
            request = requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variable},
            )

        return request.json()["data"]["userProfile"], request.json()["data"][
            "userMeta"
        ]
    except Exception:
        return None


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
                            email
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
            request = requests.post(
                "http://gateway/graphql", json={"query": query}
            )
        return request.json()["data"]["allClubs"]
    except Exception:
        return []


# get club code from club id
def getClubCode(clubid: str) -> str | None:
    allclubs = getClubs()
    for club in allclubs:
        if club["cid"] == clubid:
            return club["code"]
    return None


# get club name from club id
def getClubNameEmail(
    clubid: str, email=False, name=True
) -> str | tuple[str, str] | None:
    allclubs = getClubs()
    for club in allclubs:
        if club["cid"] == clubid:
            if email and name:
                return club["name"], club["email"]
            elif email:
                return club["email"]
            else:
                return club["name"]
    return None


# generate event code based on time and club
def getEventCode(clubid, starttime) -> str:
    club_code = getClubCode(clubid)
    if club_code is None:
        raise ValueError("Invalid clubid")

    year = fiscalyear.FiscalYear(
        fiscalyear.FiscalDateTime.fromisoformat(
            str(starttime).split("+")[0]
        ).fiscal_year
    )
    start = year.start
    end = year.end

    club_events = eventsdb.find(
        {
            "clubid": clubid,
            "datetimeperiod": {
                "$gte": start.isoformat(),
                "$lte": end.isoformat(),
            },
        }
    )

    event_count = len(list(club_events)) + 1
    code_year = str(year.fiscal_year - 1)[-2:] + str(year.fiscal_year)[-2:]

    return f"{club_code}{code_year}{event_count:03d}"  # format: CODE20XX00Y


# get link to event (based on code)
def getEventLink(code) -> str:
    host = os.environ.get("HOST", "http://localhost")
    return f"{host}/manage/events/code/{code}"


# get email IDs of all members belonging to a role
def getRoleEmails(role: str) -> List[str]:
    try:
        query = """
            query Query($role: String!, $interCommunicationSecret: String) {
              usersByRole(role: $role, interCommunicationSecret: $interCommunicationSecret) {
                uid
              }
            }
        """  # noqa: E501
        variables = {
            "role": role,
            "interCommunicationSecret": inter_communication_secret,
        }
        request = requests.post(
            "http://gateway/graphql",
            json={"query": query, "variables": variables},
        )

        # extract UIDs
        uids = list(
            map(lambda o: o["uid"], request.json()["data"]["usersByRole"])
        )

        # get emails of each UID
        emails = []
        for uid in uids:
            query = """
                query UserProfile($userInput: UserInput) {
                  userProfile(userInput: $userInput) {
                    email
                  }
                }
            """
            variables = {"userInput": {"uid": uid}}
            request = requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variables},
            )
            emails.append(request.json()["data"]["userProfile"]["email"])

        return emails

    except Exception:
        return []


def eventsWithSorting(searchspace):
    """
    Custom sorting of events based on
    datetimeperiod with upcoming events first in ascending order
    and then past events in descending order
    """
    ist = pytz.timezone("Asia/Kolkata")
    current_datetime = datetime.now(ist).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    upcoming_events_query = {
        **searchspace,
        "datetimeperiod.0": {"$gte": current_datetime},
    }
    past_events_query = {
        **searchspace,
        "datetimeperiod.0": {"$lt": current_datetime},
    }

    upcoming_events = list(
        eventsdb.find(upcoming_events_query).sort("datetimeperiod.0", 1)
    )
    past_events = list(
        eventsdb.find(past_events_query).sort("datetimeperiod.0", -1)
    )
    events = upcoming_events + past_events

    return events
