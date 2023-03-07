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
    user.update({ "clubs": ["2"], "role": None }) # TODO : remove after testing
    if (
        event is None or (
            event["status"]["state"] not in { Event_State_Status.approved, Event_State_Status.completed, } and (
                user is None or (
                    user["role"] not in { "cc", "slc", "slo" } and
                    event["clubid"] not in user["clubs"]
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
    user.update({ "clubs": [], "role": "cc" }) # TODO : remove after testing

    restrictAccess = True
    if user is not None :
        if user["role"] in { "cc", "slc", "slo" } or clubid in user["clubs"] :
            restrictAccess = False

    searchspace = dict()
    if clubid is not None :
        searchspace["clubid"] = clubid
    if restrictAccess :
        searchspace["status.state"] = { "$in": [ Event_State_Status.approved.value, Event_State_Status.completed.value ] }

    events = eventsdb.find(searchspace)
    return [EventType.from_pydantic(Event.parse_obj(event)) for event in events]


# register all queries
queries = [
    getEvent,
    # getIncompleteEvents,
    # getApprovedEvents,
    # getPendingEvents,
    getAllEvents,
]
