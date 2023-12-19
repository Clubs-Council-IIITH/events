import strawberry

from fastapi.encoders import jsonable_encoder
from typing import List, Tuple
from datetime import datetime
import dateutil.parser as dp
import requests

from db import eventsdb

# import all models and types
from models import Event
from otypes import Info, EventType, RoomList, RoomListType
from mtypes import Event_State_Status, Event_Location

from utils import getClubs


@strawberry.field
def event(eventid: str, info: Info) -> EventType:
    """
    return event with given id if it is visible to the user
    """
    user = info.context.user
    event = eventsdb.find_one({"_id": eventid})

    allclubs = getClubs(info.context.cookies)
    list_allclubs = list()
    for club in allclubs:
        list_allclubs.append(club["cid"])

    if (
        event is None
        or (
            event["status"]["state"]
            not in {
                Event_State_Status.approved.value,
            }
            and (
                user is None
                or (
                    user["role"] not in {"cc", "slc", "slo"}
                    and (user["role"] != "club" or user["uid"] != event["clubid"])
                )
            )
        )
        or event["clubid"] not in list_allclubs
    ):
        raise Exception(
            "Can not access event. Either it does not exist or user does not have perms."
        )

    return EventType.from_pydantic(Event.parse_obj(event))


@strawberry.field
def eventid(code: str, info: Info) -> str:
    """
    return eventid given event code
    """

    event = eventsdb.find_one({"code": code})

    if event is None:
        raise Exception("Event with given code does not exist.")

    return event["_id"]


@strawberry.field
def events(
    clubid: str | None, 
    info: Info,
    paginationOn: bool = True,
    skip: int = 0,
    limit: int = 0
    ) -> List[EventType]:
    """
    return all events visible to the user
    if clubid is specified, then return events of that club only
    """
    if limit == 0 and skip == 0:
        paginationOn = False

    user = info.context.user

    restrictAccess = True
    restrictCCAccess = True
    if user is not None:
        if user["role"] in {"cc", "slc", "slo"} or (
            user["role"] == "club" and user["uid"] == clubid
        ):
            restrictAccess = False
            if not user["role"] in {"slc", "slo"}:
                restrictCCAccess = False

    searchspace = dict()
    if clubid is not None:
        searchspace["clubid"] = clubid
    else:
        allclubs = getClubs(info.context.cookies)
        list_allclubs = list()
        for club in allclubs:
            list_allclubs.append(club["cid"])
        searchspace["clubid"] = {"$in": list_allclubs}
    if restrictAccess:
        searchspace["status.state"] = {
            "$in": [
                Event_State_Status.approved.value,
            ]
        }
        searchspace["audience"] = {"$nin": ["internal"]}
    elif restrictCCAccess:
        searchspace["status.state"] = {
            "$in": [
                Event_State_Status.approved.value,
                Event_State_Status.pending_budget.value,
                Event_State_Status.pending_room.value,
            ]
        }

    if paginationOn:
        events = eventsdb.find(searchspace).sort("datetimeperiod", -1).skip(skip).limit(limit)
    else:
        events = eventsdb.find(searchspace).sort("datetimeperiod", -1)

    return [EventType.from_pydantic(Event.parse_obj(event)) for event in events]

# TODO: this is a temporary query; remove it later once pagination has been implemented for the `events` query
@strawberry.field
def recentEvents(info: Info) -> List[EventType]:
    """
    return the recent 10 events across all clubs
    only publicly visible events are returned
    """
    user = info.context.user

    searchspace = dict()
    searchspace["status.state"] = {
        "$in": [
            Event_State_Status.approved.value,
        ]
    }
    searchspace["audience"] = {"$nin": ["internal"]}

    allclubs = getClubs(info.context.cookies)
    list_allclubs = list()
    for club in allclubs:
        list_allclubs.append(club["cid"])
    searchspace["clubid"] = {"$in": list_allclubs}

    current_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00")
    upcoming_events_query = {
        **searchspace,
        "datetimeperiod.0": {"$gte": current_datetime}
    }
    past_events_query = {
        **searchspace,
        "datetimeperiod.0": {"$lt": current_datetime}
    }

    upcoming_events = list(eventsdb.find(upcoming_events_query).sort("datetimeperiod.0", 1))
    past_events = list(eventsdb.find(past_events_query).sort("datetimeperiod.0", -1))
    events = upcoming_events + past_events

    return [EventType.from_pydantic(Event.parse_obj(event)) for event in events[:12]]


@strawberry.field
def incompleteEvents(clubid: str, info: Info) -> List[EventType]:
    """
    return all incomplete events of a club
    raise Exception if user is not a member of the club
    """
    user = info.context.user

    if not user or user["role"] != "club" or user["uid"] != clubid:
        raise Exception("You do not have permission to access this resource.")

    events = eventsdb.find(
        {
            "clubid": clubid,
            "status.state": Event_State_Status.incomplete.value,
        }
    )

    # sort events in ascending order of time
    events = sorted(
        events,
        key=lambda event: event["datetimeperiod"][0],
        reverse=False,
    )

    return [EventType.from_pydantic(Event.parse_obj(event)) for event in events]


@strawberry.field
def approvedEvents(
    clubid: str | None, 
    info: Info,
    paginationOn: bool = True,
    skip: int = 0,
    limit: int = 0
    ) -> List[EventType]:
    """
    if clubid is set, return approved events of that club.
    else return approved events of every club.
    NOTE: this is a public query, accessible to all.
    """
    if limit == 0 and skip == 0:
        paginationOn = False
    
    user = info.context.user

    requested_state = Event_State_Status.approved.value

    searchspace = {
        "status.state": requested_state,
    }
    if clubid is not None:
        searchspace["clubid"] = clubid
    else:
        allclubs = getClubs(info.context.cookies)
        list_allclubs = list()
        for club in allclubs:
            list_allclubs.append(club["cid"])
        searchspace["clubid"] = {"$in": list_allclubs}

    searchspace["audience"] = {"$nin": ["internal"]}

    if paginationOn:
        events = eventsdb.find(searchspace).sort("datetimeperiod", -1).skip(skip).limit(limit)
    else:
        events = eventsdb.find(searchspace).sort("datetimeperiod", -1)

    return [EventType.from_pydantic(Event.parse_obj(event)) for event in events]


@strawberry.field
def pendingEvents(clubid: str | None, info: Info) -> List[EventType]:
    """
    if user is admin, return events pending for them
    if InpClub is set, and current user belongs to that club,
    return pending events of that club.
    raise Exception if user is not adimn and user is not in that club.
    """
    user = info.context.user

    requested_states = set()
    searchspace = dict()
    if user is not None:
        if "cc" == user["role"]:
            requested_states |= {Event_State_Status.pending_cc.value}
        if "slc" == user["role"]:
            requested_states |= {Event_State_Status.pending_budget.value}
        if "slo" == user["role"]:
            requested_states |= {Event_State_Status.pending_room.value}
            searchspace["status.budget"] = True
        if "club" == user["role"] and user["uid"] == clubid:
            requested_states |= {
                Event_State_Status.incomplete.value,
                Event_State_Status.pending_cc.value,
                Event_State_Status.pending_budget.value,
                Event_State_Status.pending_room.value,
            }
    requested_states = list(requested_states)

    if user is None or len(requested_states) == 0:
        raise Exception("You do not have permission to access this resource.")

    searchspace["status.state"] = {
        "$in": requested_states,
    }
    if clubid is not None:
        searchspace["clubid"] = clubid

    events = eventsdb.find(searchspace)

    # sort events in ascending order of time
    events = sorted(
        events,
        key=lambda event: event["datetimeperiod"][0],
        reverse=False,
    )

    return [EventType.from_pydantic(Event.parse_obj(event)) for event in events]


@strawberry.field
def availableRooms(timeslot: Tuple[datetime, datetime], eventid: str | None, info: Info) -> RoomListType:
    """
    return a list of all rooms that are available in the given timeslot
    NOTE: this is a public query, accessible to all.
    """
    user = info.context.user
    assert timeslot[0] < timeslot[1], "Invalid timeslot"

    approved_events = eventsdb.find(
        {
            "status.state": Event_State_Status.approved.value,
        },
        {
            "location": 1,
            "datetimeperiod": 1,
        },
    )

    free_rooms = set(Event_Location)
    for approved_event in approved_events:
        start_time = dp.parse(approved_event["datetimeperiod"][0])
        end_time = dp.parse(approved_event["datetimeperiod"][1])
        if timeslot[1] >= start_time and timeslot[0] <= end_time:
            free_rooms.difference_update(approved_event["location"])
    
    if eventid is not None:
        event = eventsdb.find_one({"_id": eventid})
        if event is not None:
            free_rooms.update(event["location"])

    return RoomListType.from_pydantic(RoomList.parse_obj({"locations": free_rooms}))


# register all queries
queries = [
    event,
    events,
    eventid,
    recentEvents,
    incompleteEvents,
    approvedEvents,
    pendingEvents,
    availableRooms,
]
