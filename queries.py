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
    
    eventclass = Event.parse_obj(event)
    return EventType.from_pydantic(eventclass)


# register all queries
queries = [
    getEvent,
#    getIncompleteEvents,
#    getApprovedEvents,
#    getPendingEvents,
#    getAllEvents,
]
