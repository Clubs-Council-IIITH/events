import os
import requests
import fiscalyear

from typing import List
from datetime import datetime, timedelta

from db import eventsdb

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
                "http://gateway/graphql", json={"query": query, "variables": variables}
            )
        return request.json()["data"]["member"]

    except:
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


# get club name from club id
def getClubNameEmail(clubid: str, email = False, name = True) -> str | None:
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
def getEventCode(clubid):
    club_code = getClubCode(clubid)
    year = fiscalyear.FiscalYear.current().fiscal_year
    club_events = eventsdb.find(
        {
            "clubid": clubid,
            "datetimeperiod": {
                "$gte": (datetime.now() - timedelta(days=2 * 365)).isoformat()
            },
        }
    )

    event_count = 0
    for c_event in club_events:
        if (
            fiscalyear.FiscalDateTime.fromisoformat(
                c_event["datetimeperiod"][0].split("+")[
                    0
                ]  # remove timezone because UTC
            ).fiscal_year
            == year
        ):
            event_count += 1

    if club_code is None:
        raise ValueError("Invalid clubid")

    return f"{club_code}{year}{event_count:03d}"  # format: CODE20XX00Y


# get link to event (based on code)
def getEventLink(code) -> str:
    host = os.environ.get("HOST", "http://localhost")
    return f"{host}/manage/events/code/{code}"


# get email IDs of all members belonging to a role
def getRoleEmails(role: str) -> List[str]:
    try:
        query = """
            query Query($role: String!) {
              usersByRole(role: $role) {
                uid
              }
            }
        """
        variables = {"role": role}
        request = requests.post(
            "http://gateway/graphql", json={"query": query, "variables": variables}
        )

        # extract UIDs
        uids = list(map(lambda o: o["uid"], request.json()["data"]["usersByRole"]))

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
                "http://gateway/graphql", json={"query": query, "variables": variables}
            )
            emails.append(request.json()["data"]["userProfile"]["email"])

        return emails

    except:
        return []
