import strawberry

from fastapi.encoders import jsonable_encoder
from typing import List
from db import db
eventsdb = db.events

# import all models and types
from models import Event
from otypes import Info, EventType, InputClubId, InputEventId
from mtypes import Event_State_Status


@strawberry.field
def getEvent (InpEvent: InputEventId, info: Info) -> EventType:
    '''
        return event with given id if it is visible to the user
    '''

    user = info.context.user
    eventid = InpEvent.to_pydantic().id

    event = eventsdb.find_one({"_id": eventid})

    if (
        event is None or (
            event["status.state"] not in { Event_State_Status.approved, Event_State_Status.completed, } and (
                user is None or (
                    user["role"] not in { "cc", "slc", "slo" } and
                    event["club"] not in user["clubs"]
                )
            )
        )
    ) :
        raise Exception("Can not access event. Either it does not exist or user does not have perms.")

    return EventType.from_pydantic(Event.parse_obj(event))

@strawberry.field
def getIncompleteEvents (InpClub: InputClubId, info: Info) -> List[EventType]:
    '''
        return all incomplete events of a club
        raise Exception if user is not a member of the club
    '''

    user = info.context.user
    clubid = InpClub.to_pydantic().clubid

    if not user or clubid not in user["clubs"] :
        raise Exception(
            "You do not have permission to access this resource."
        )

    events = eventsdb.find({
        "clubid": clubid,
        "status.state": Event_State_Status.incomplete,
    })
    return [EventType.from_pydantic(Event.parse_obj(event)) for event in events]

@strawberry.field
def getApprovedEvents (InpClub: InputClubId | None, info: Info) -> List[EventType]:
    '''
        if InpClub is set, and current user belongs to that club,
        return approved events of that club.
        else return approved events of every club.
        raise Exception if InpClub is set and user is not in that club.
        TODO: what to do for admins
    '''

    user = info.context.user
    clubid = None
    if InpClub:
        clubid = InpClub.to_pydantic().clubid

    requested_state = Event_State_Status.approved

    # default searchspace if clubid is not set
    searchspace = {
        "status.state": requested_state
    }

    if clubid :
        if not user or clubid not in user["clubs"] :
            # raise this Exception if clubid is set and
            # either user is not set or user is not in that club
            raise Exception(
                "You do not have permission to access this resource."
            )
        # searchspace if clubid is set and valid
        searchspace = {
            "clubid": clubid,
            "status.state": requested_state,
        }

    return [EventType.from_pydantic(Event.parse_obj(event)) for event in eventsdb.find(searchspace)]

@strawberry.field
def getPendingEvents (InpClub: InputClubId, info: Info) -> List[EventType]:
    '''
        if user is admin, return events pending for them
        if InpClub is set, and current user belongs to that club,
        return pending events of that club.
        raise Exception if user is not in that club.
    '''

    user = info.context.user
    clubid = InpClub.to_pydantic().clubid

    requested_states = set()
    if user :
        if "cc" == user["role"] :
            requested_states |= {Event_State_Status.pending_cc}
        if "slc" == user["role"] :
            requested_states |= {Event_State_Status.pending_budget}
        if "slo" == user["role"] :
            requested_states |= {Event_State_Status.pending_room}
        if clubid in user["clubs"] :
            requested_states |= {Event_State_Status.pending_cc, Event_State_Status.pending_budget, Event_State_Status.pending_room}

    if not user or len(requested_states) == 0 :
        raise Exception(
            "You do not have permission to access this resource."
        )

    # default searchspace if clubid is not set
    searchspace = {
        "status.state": { "$in": requested_states }
    }

    return [EventType.from_pydantic(Event.parse_obj(event)) for event in eventsdb.find(searchspace)]

@strawberry.field
def getAllEvents (InpClub: InputClubId | None, info: Info) -> List[EventType]:
    '''
        return all events visible to the user
        if clubid is specified, then return events of that club only
    '''

    user = info.context.user
    clubid = InpClub.to_pydantic().clubid if InpClub else None

    restrictAccess = True
    if user is not None :
        if user["role"] in { "cc", "slc", "slo" } or clubid in user["clubs"] :
            restrictAccess = False

    searchspace = dict()
    if clubid is not None :
        searchspace["clubid"] = clubid
    if restrictAccess :
        searchspace["status.state"] = { "$in": [ Event_State_Status.approved, Event_State_Status.completed ] }
    events = eventsdb.find(searchspace)

    return [EventType.from_pydantic(Event.parse_obj(event)) for event in events]


# register all queries
queries = [
    getEvent,
    getIncompleteEvents,
    getApprovedEvents,
    getPendingEvents,
    getAllEvents,
]
