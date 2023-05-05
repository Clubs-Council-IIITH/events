import strawberry

from fastapi.encoders import jsonable_encoder
from typing import List, Tuple
from datetime import datetime
import dateutil.parser as dp

from db import eventsdb
from bson import ObjectId

# import all models and types
from models import Event
from otypes import Info, EventType, RoomList, RoomListType
from mtypes import Event_State_Status, Event_Location, PyObjectId


@strawberry.field
def event(eventid: str, info: Info) -> EventType:
    """
    return event with given id if it is visible to the user
    """
    user = info.context.user
    event = eventsdb.find_one({"_id": ObjectId(eventid)})

    allevents = eventsdb.find({})

    if event is None or (
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
    ):
        raise Exception(
            "Can not access event. Either it does not exist or user does not have perms."
        )

    return EventType.from_pydantic(Event.parse_obj(event))


@strawberry.field
def events(clubid: str | None, info: Info) -> List[EventType]:
    """
    return all events visible to the user
    if clubid is specified, then return events of that club only
    """
    user = info.context.user

    restrictAccess = True
    if user is not None:
        if user["role"] in {"cc", "slc", "slo"} or (
            user["role"] == "club" and user["uid"] == clubid
        ):
            restrictAccess = False

    searchspace = dict()
    if clubid is not None:
        searchspace["clubid"] = clubid
    if restrictAccess:
        searchspace["status.state"] = {
            "$in": [
                Event_State_Status.approved.value,
            ]
        }

    events = eventsdb.find(searchspace)
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

    events = eventsdb.find(searchspace)

    # sort events in descending order of time
    events = sorted(
        events,
        key=lambda event: event["datetimeperiod"][0],
        reverse=True,
    )

    return [EventType.from_pydantic(Event.parse_obj(event)) for event in events[:10]]


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
    return [EventType.from_pydantic(Event.parse_obj(event)) for event in events]


@strawberry.field
def approvedEvents(clubid: str | None, info: Info) -> List[EventType]:
    """
    if clubid is set, return approved events of that club.
    else return approved events of every club.
    NOTE: this is a public query, accessible to all.
    """
    user = info.context.user

    requested_state = Event_State_Status.approved.value

    searchspace = {
        "status.state": requested_state,
    }
    if clubid is not None:
        searchspace["clubid"] = clubid

    events = eventsdb.find(searchspace)
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
    if user is not None:
        if "cc" == user["role"]:
            requested_states |= {Event_State_Status.pending_cc.value}
        if "slc" == user["role"]:
            requested_states |= {Event_State_Status.pending_budget.value}
        if "slo" == user["role"]:
            requested_states |= {Event_State_Status.pending_room.value}
        if "club" == user["role"] and user["uid"] == clubid:
            requested_states |= {
                Event_State_Status.pending_cc.value,
                Event_State_Status.pending_budget.value,
                Event_State_Status.pending_room.value,
            }
    requested_states = list(requested_states)

    if user is None or len(requested_states) == 0:
        raise Exception("You do not have permission to access this resource.")

    searchspace = {
        "status.state": {"$in": requested_states},
    }
    if clubid is not None:
        searchspace["clubid"] = clubid

    events = eventsdb.find(searchspace)
    return [EventType.from_pydantic(Event.parse_obj(event)) for event in events]


@strawberry.field
def availableRooms(timeslot: Tuple[datetime, datetime], info: Info) -> RoomListType:
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
        if (
            timeslot[1] > start_time
            and timeslot[0] < end_time
        ):
            free_rooms.difference_update(approved_event['location'])

    return RoomListType.from_pydantic(RoomList.parse_obj({"locations": free_rooms}))


# register all queries
queries = [
    event,
    events,
    recentEvents,
    incompleteEvents,
    approvedEvents,
    pendingEvents,
    availableRooms,
]
