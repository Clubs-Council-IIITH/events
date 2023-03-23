import strawberry

from fastapi.encoders import jsonable_encoder
from typing import List
from db import eventsdb

# import all models and types
from models import Event
from otypes import Info, EventType
from mtypes import Event_State_Status, PyObjectId


@strawberry.field
def getEvent (eventid: str, info: Info) -> EventType:
    '''
        return event with given id if it is visible to the user
    '''
    user = info.context.user
    event = eventsdb.find_one({"_id": eventid})
    
    user = dict() # TODO : remove after testing
    user.update({ "uid": "a@iiit.ac.in", "role": "club" }) # TODO : remove after testing
    if (
        event is None or (
            event["status"]["state"] not in { Event_State_Status.approved.value, Event_State_Status.completed.value, } and (
                user is None or (
                    user["role"] not in { "cc", "slc", "slo" } and
                    (
                        user["role"] != "club" or
                        user["uid"] != event["clubid"]
                    )
                )
            )
        )
    ) :
         raise Exception("Can not access event. Either it does not exist or user does not have perms.")
    
    return EventType.from_pydantic(Event.parse_obj(event))

@strawberry.field
def getAllEvents (clubid: str | None, info: Info) -> List[EventType]:
    '''
        return all events visible to the user
        if clubid is specified, then return events of that club only
    '''
    user = info.context.user

    user = dict() # TODO : remove after testing
    user.update({ "uid": "a@iiit.ac.in", "role": "club" }) # TODO : remove after testing

    restrictAccess = True
    if user is not None :
        if user["role"] in { "cc", "slc", "slo" } or ( user["role"] == "club" and user["uid"] == clubid ) :
            restrictAccess = False

    searchspace = dict()
    if clubid is not None :
        searchspace["clubid"] = clubid
    if restrictAccess :
        searchspace["status.state"] = { "$in": [ Event_State_Status.approved.value, Event_State_Status.completed.value ] }

    events = eventsdb.find(searchspace)
    return [EventType.from_pydantic(Event.parse_obj(event)) for event in events]

@strawberry.field
def getIncompleteEvents (clubid: str, info: Info) -> List[EventType]:
    '''
        return all incomplete events of a club
        raise Exception if user is not a member of the club
    '''
    user = info.context.user

    user = dict() # TODO : remove after testing
    user.update({ "uid": "a@iiit.ac.in", "role": "club" }) # TODO : remove after testing

    if not user or user["role"] != "club" or user["uid"] != clubid :
        raise Exception(
            "You do not have permission to access this resource."
        )

    events = eventsdb.find({
        "clubid": clubid,
        "status.state": Event_State_Status.incomplete.value,
    })
    return [EventType.from_pydantic(Event.parse_obj(event)) for event in events]

@strawberry.field
def getApprovedEvents (clubid: str | None, info: Info) -> List[EventType]:
    '''
        if clubid is set, return approved events of that club.
        else return approved events of every club.
        NOTE: this is a public query, accessible to all.
    '''
    user = info.context.user

    requested_state = Event_State_Status.approved.value

    searchspace = {
        "status.state": requested_state,
    }
    if clubid is not None :
        searchspace["clubid"] = clubid

    events = eventsdb.find(searchspace)
    return [EventType.from_pydantic(Event.parse_obj(event)) for event in events]

@strawberry.field
def getPendingEvents (clubid: str | None, info: Info) -> List[EventType]:
    '''
        if user is admin, return events pending for them
        if InpClub is set, and current user belongs to that club,
        return pending events of that club.
        raise Exception if user is not adimn and user is not in that club.
    '''
    user = info.context.user

    user = dict() # TODO : remove after testing
    user.update({ "uid": "a@iiit.ac.in", "role": "club" }) # TODO : remove after testing

    requested_states = set()
    if user is not None :
        if "cc" == user["role"] :
            requested_states |= {Event_State_Status.pending_cc.value}
        if "slc" == user["role"] :
            requested_states |= {Event_State_Status.pending_budget.value}
        if "slo" == user["role"] :
            requested_states |= {Event_State_Status.pending_room.value}
        if "club" == user["role"] and user["uid"] == clubid :
            requested_states |= {Event_State_Status.pending_cc.value, Event_State_Status.pending_budget.value, Event_State_Status.pending_room.value}

    if user is None or len(requested_states) == 0 :
        raise Exception(
            "You do not have permission to access this resource."
        )

    searchspace = {
        "status.state": { "$in": requested_states },
    }
    if clubid is not None :
        searchspace["clubid"] = clubid

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
