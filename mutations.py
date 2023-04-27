import strawberry

from fastapi.encoders import jsonable_encoder

from db import eventsdb
from bson import ObjectId

# import all models and types
from models import Event
from otypes import Info, InputEventDetails, EventType
from mtypes import (
    Event_Mode,
    Event_Location,
    Audience,
    Event_State_Status,
)


@strawberry.mutation
def createEvent(details: InputEventDetails, info: Info) -> EventType:
    """
    create event with given details if user has permission
    return the event
    """
    user = info.context.user

    if (
        not user
        or not details.clubid
        or (user["role"] != "club" or user["uid"] != details.clubid)
    ):
        raise Exception("You do not have permission to access this resource.")

    event_instance = Event(
        name=details.name,
        clubid=details.clubid,
        datetimeperiod=details.datetimeperiod,
    )
    if details.mode is not None:
        event_instance.mode = Event_Mode(details.mode)
    if details.location is not None:
        event_instance.location = [Event_Location(loc) for loc in details.location]
    if details.description is not None:
        event_instance.description = details.description
    if details.poster is not None:
        event_instance.poster = details.poster
    if details.audience is not None:
        event_instance.audience = [Audience(aud) for aud in details.audience]
    if details.link is not None:
        event_instance.link = details.link
    if details.equipment is not None:
        event_instance.equipment = details.equipment
    if details.additional is not None:
        event_instance.additional = details.additional
    if details.population is not None:
        event_instance.population = details.population
    if details.budget is not None:
        event_instance.budget = details.budget

    created_id = eventsdb.insert_one(jsonable_encoder(event_instance)).inserted_id
    created_event = Event.parse_obj(eventsdb.find_one({"_id": ObjectId(created_id)}))

    return EventType.from_pydantic(created_event)


@strawberry.mutation
def progressEvent(
    eventid: str,
    info: Info,
    cc_progress_budget: bool = False,
    cc_progress_room: bool = False,
) -> EventType:
    """
    progress the event state status for different users
    returns the new event details

    initially, the event is `incomplete`
    after the club fills all the details, they progress it
    cc chooses to progress the state status, the budget status and the room status
    if budget status is unapproved, the event is `pending_budget`, else skip to next
    after budget is approved (through any track),
    if room status is unapproved, the event is `pending_room`, else skip to next
    after room is approved (through any track), the event is `approved`
    once the event is over, the club or cc can change the state to `completed`
    """
    noaccess_error = Exception(
        "Can not access event. Either it does not exist or user does not have perms."
    )

    user = info.context.user

    event_ref = eventsdb.find_one({"_id": ObjectId(eventid)})
    if event_ref is None or user is None:
        raise noaccess_error
    event_instance = Event.parse_obj(event_ref)

    status_updation = dict()

    if event_instance.status.state == Event_State_Status.incomplete:
        if user["role"] != "club" or user["uid"] != event_instance.clubid:
            raise noaccess_error
        updation = {
            "budget": False,
            "room": False,
            "state": Event_State_Status.pending_cc.value,
        }

    elif event_instance.status.state == Event_State_Status.pending_cc:
        if user["role"] != "cc":
            raise noaccess_error
        updation = {
            "budget": cc_progress_budget
            or sum([b.amount for b in event_instance.budget]) == 0,
            "room": cc_progress_room or len(event_instance.location) == 0,
        }

        if not updation["budget"]:
            updation["state"] = Event_State_Status.pending_budget.value
        elif not updation["room"]:
            updation["state"] = Event_State_Status.pending_room.value
        else:
            updation["state"] = Event_State_Status.approved.value

    elif event_instance.status.state == Event_State_Status.pending_budget:
        if user["role"] != "slc":
            raise noaccess_error
        assert event_instance.status.budget == False
        updation = {
            "budget": True,
            "room": event_instance.status.room | len(event_instance.location) == 0,
        }

        if not updation["room"]:
            updation["state"] = Event_State_Status.pending_room.value
        else:
            updation["state"] = Event_State_Status.approved.value

    elif event_instance.status.state == Event_State_Status.pending_room:
        if user["role"] != "slo":
            raise noaccess_error
        assert event_instance.status.budget == True
        assert event_instance.status.room == False
        updation = {
            "budget": event_instance.status.budget,
            "room": True,
            "state": Event_State_Status.approved.value,
        }

    elif event_instance.status.state == Event_State_Status.approved:
        if user["role"] != "cc" and (
            user["role"] != "club" or user["uid"] != event_instance.clubid
        ):
            raise noaccess_error

        updation = {
            "budget": event_instance.status.budget,
            "room": event_instance.status.room,
            "state": Event_State_Status.approved.value,
        }

    eventsdb.update_one({"_id": ObjectId(eventid)}, {"$set": {"status": updation}})
    return EventType.from_pydantic(event_instance)


@strawberry.mutation
def deleteEvent(eventid: str, info: Info) -> EventType:
    """
    change the state of the event to `deleted` if the user has permissions
    """
    user = info.context.user

    if user["role"] in [
        "cc",
    ]:
        query = {
            "_id": ObjectId(eventid),
        }
    else:
        query = {
            "_id": ObjectId(eventid),
            "clubid": user["uid"],
        }

    updation = {
        "$set": {
            "status": {
                "state": Event_State_Status.deleted.value,
                "budget": False,
                "room": False,
            }
        }
    }

    upd_ref = eventsdb.update_one(query, updation)
    if upd_ref.matched_count == 0:
        raise Exception(
            "Can not access event. Either it does not exist or user does not have perms."
        )

    event_ref = eventsdb.find_one({"_id": ObjectId(eventid)})
    return EventType.from_pydantic(Event.parse_obj(event_ref))


# register all mutations
mutations = [
    createEvent,
    progressEvent,
    deleteEvent,
]
