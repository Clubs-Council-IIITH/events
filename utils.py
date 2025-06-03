import html
import os
import re
from datetime import datetime
from typing import List

import fiscalyear
import requests

from db import eventsdb
from mtypes import timezone
from otypes import timelot_type

inter_communication_secret = os.getenv("INTER_COMMUNICATION_SECRET")

# start month of financial year
FISCAL_START_MONTH = 4

# fiscalyear config
fiscalyear.START_MONTH = FISCAL_START_MONTH


def getMember(cid, uid, cookies=None) -> dict | None:
    """
    This function makes a query to the Members service resolved by the
    member method, fetches info about a member.

    Args:
        cid (str): club id
        uid (str): user id
        cookies (dict): cookies. Defaults to None.

    Returns:
        (dict|None): response of the request
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


def getUser(uid, cookies=None) -> dict | None:
    """
    Function makes a query to the Users service resolved by the userProfile
    method, fetches info about a user.

    Args:
        uid (str): user id
        cookies (dict): cookies. Defaults to None.

    Returns:
        (dict | None): response of the request
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


def getClubs(cookies=None) -> dict:
    """
    Function to call a query to the Clubs service resolved by the allClubs
    method, fetches info about all clubs.

    Args:
        cookies (dict): cookies. Defaults to None.

    Returns:
        (dict): responce of the request
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


# method gets club code from club id
def getClubCode(clubid: str) -> str | None:
    """
    Fetches the code of the club whose club id is given.

    Args:
        clubid (str): club id

    Returns:
        (str | None): club code or None if club not found
    """
    allclubs = getClubs()
    for club in allclubs:
        if club["cid"] == clubid:
            return club["code"]
    return None


def getClubDetails(
    clubid: str,
    cookies,
) -> dict:
    """
    This method makes a query to the clubs service resolved by the club
    method, used to get a club's name from its clubid.

    Args:
        clubid (str): club id
        cookies (dict): cookies

    Returns:
        (dict): response of the request
    """

    try:
        query = """
                    query Club($clubInput: SimpleClubInput!) {
                        club(clubInput: $clubInput) {
                            cid
                            name
                            email
                            category
                        }
                    }
                """
        variable = {"clubInput": {"cid": clubid}}
        request = requests.post(
            "http://gateway/graphql",
            json={"query": query, "variables": variable},
            cookies=cookies,
        )
        return request.json()["data"]["club"]
    except Exception:
        return {}


def getEventCode(clubid, starttime) -> str:
    """
    generate event code based on starttime and organizing club

    Args:
        clubid (str): club id
        starttime (datetime): start time of the event

    Returns:
        (str): event code

    Raises:
        ValueError: Invalid clubid
    """

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

    max_code = 0
    for i in list(club_events):
        code = i["code"]
        code = int(code[-3:])
        if code > max_code:
            max_code = code

    event_count = max_code + 1
    code_year = str(year.fiscal_year - 1)[-2:] + str(year.fiscal_year)[-2:]

    return f"{club_code}{code_year}{event_count:03d}"  # format: CODE20XX00Y


# method produces link to event (based on code as input)
# It returns a link to the event page
def getEventLink(code) -> str:
    """
    Produces a link to the event page based on the event code.

    Args:
        code (str): event code

    Returns:
        (str): link to the event page
    """
    host = os.environ.get("HOST", "http://localhost")
    return f"{host}/manage/events/code/{code}"


# method to get the event finances page link for SLO
# It returns a link to the event finances page
def getEventFinancesLink(id) -> str:
    """
    Produces a link to the event finances page based on the event id.

    Args:
        id (str): event id

    Returns:
        (str): link to the event finances page
    """
    host = os.environ.get("HOST", "http://localhost")
    return f"{host}/manage/finances/{id}"


# get email IDs of all members belonging to a role
def getRoleEmails(role: str) -> List[str]:
    """
    Brings all the emails of members belonging to a role

    Args:
        role: role of the user to be searched

    Returns:
        (List[str]): list of emails.
    """

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


def eventsWithSorting(
    searchspace,
    name: str | None = None,
    date_filter=False,
    pagination=False,
    skip=0,
    limit: int | None = None,
    timings: timelot_type | None = None,
) -> List[dict]:
    """
    Provides a list of events based on the searchspace provided.

    Custom sorting of events based on
    datetimeperiod with
    ongoing events first in ascending order of end time
    then
    upcoming events first in ascending order of start time
    and then
    past events in descending order of end time
    It also filters events based on name if name is provided and
    pagination is True.

    Args:
        searchspace (dict): search space for events
        name (str): name of the event. Defaults to None.
        date_filter (bool): if True, filters events based on date.
                            Defaults to False.
        pagination (bool): if True, paginates the events. Defaults to False.
        skip (int): number of events to skip
        limit (int): number of events to return. Defaults to None.
        timings (timelot_type | None): The time period for which the events
                                are to be fetched. Defaults to None.

    Returns:
        (List[dict]): list of events
    """
    current_datetime = datetime.now(timezone).strftime(
        "%Y-%m-%dT%H:%M:%S+00:00"
    )

    if date_filter:
        required_events_query = {
            **searchspace,
        }
        events = list(
            eventsdb.find(required_events_query).sort("datetimeperiod.0", -1)
        )
        return events

    if name is not None and pagination:
        searchspace["name"] = {"$regex": name, "$options": "i"}

    if timings is not None:
        timings_str = [
            timings[0].strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            timings[1].strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        ]
        timings_conditions = [
            # Event starts within the timing period
            {
                "datetimeperiod.0": {
                    "$gte": timings_str[0],
                    "$lt": timings_str[1],
                }
            },
            # Event ends within the timing period
            {
                "datetimeperiod.1": {
                    "$gt": timings_str[0],
                    "$lte": timings_str[1],
                }
            },
            # Event spans the entire timing period
            {
                "datetimeperiod.0": {"$lte": timings_str[0]},
                "datetimeperiod.1": {"$gte": timings_str[1]},
            },
        ]

        searchspace = {
            **searchspace,
            "$or": timings_conditions,
        }

    ongoing_events_query = {
        **searchspace,
        "datetimeperiod.0": {"$lte": current_datetime},
        "datetimeperiod.1": {"$gte": current_datetime},
    }
    upcoming_events_query = {
        **searchspace,
        "datetimeperiod.0": {"$gt": current_datetime},
    }
    past_events_query = {
        **searchspace,
        "datetimeperiod.1": {"$lt": current_datetime},
    }

    if pagination:
        if skip < 0:
            ongoing_events = list(
                eventsdb.find(ongoing_events_query).sort(
                    "datetimeperiod.0", -1
                )
            )
            upcoming_events = list(
                eventsdb.find(upcoming_events_query).sort(
                    "datetimeperiod.0", 1
                )
            )

            events = ongoing_events + upcoming_events
        else:
            past_events = list(
                eventsdb.find(past_events_query)
                .sort("datetimeperiod.1", -1)
                .skip(skip)
                .limit(limit)
            )
            events = past_events
    else:
        ongoing_events = list(
            eventsdb.find(ongoing_events_query).sort("datetimeperiod.0", -1)
        )
        upcoming_events = list(
            eventsdb.find(upcoming_events_query).sort("datetimeperiod.0", 1)
        )
        past_events = list(
            eventsdb.find(past_events_query).sort("datetimeperiod.1", -1)
        )

        events = ongoing_events + upcoming_events + past_events
        if limit:
            events = events[:limit]

    return events


# method hides data from public viewers who view information of an event
def trim_public_events(event: dict) -> dict:
    """
    Hides certain data fields from public viewers who view information of
    an event.

    Args:
        event (dict): event to be trimmed of sensitive data

    Returns:
        (dict): trimmed event
    """
    delete_keys = [
        "equipment",
        "additional",
        "population",
        "poc",
        "budget",
        "bills_status",
    ]
    for key in delete_keys:
        if key in event:
            del event[key]

    status = event["status"]
    del event["status"]

    event["status"] = {
        "state": status["state"],
    }

    return event


# method used to convert text to html
def convert_to_html(text) -> str:
    """
    Method used to convert text to html.

    Args:
        text (str): text to be converted to html.

    Returns:
        (str): text in the form of html.
    """
    # Escape HTML special characters
    text = html.escape(text)

    # Replace URLs with HTML link tags
    url_pattern = r"(http[s]?://\S+)"
    text = re.sub(url_pattern, r'<a href="\1">\1</a>', text)

    # Replace newlines with <br> tags
    text = re.sub(r"\n", "<br>", text)

    # Replace multiple spaces with &nbsp; (non-breaking space)
    text = re.sub(r" {2,}", lambda m: "&nbsp;" * len(m.group(0)), text)

    return f"<pre>{text}</pre>"


# method used to delete a file from the file server
def delete_file(filename) -> str:
    """
    Method used to delete a file from the file service.

    Args:
        filename (str): name of the file to be deleted.

    Returns:
        (str): response from the file service.
    """
    response = requests.post(
        "http://files/delete-file",
        params={
            "filename": filename,
            "inter_communication_secret": inter_communication_secret,
        },
    )

    if response.status_code != 200:
        raise Exception(response.text)

    return response.text


def get_bot_cookie() -> dict:
    """
    Method to get the bot cookie.

    Returns:
        (dict): cookies.
    """

    response = requests.post(
        "http://auth/bot-cookie",
        json={"secret": inter_communication_secret, "uid": "events"},
    )

    return_dict = {}
    for key, value in response.cookies.items():
        return_dict[key] = value

    return return_dict
