import strawberry

from fastapi.encoders import jsonable_encoder

from db import eventsdb
from bson import ObjectId

# import all models and types
from models import Event
from otypes import Info, InputEventDetails, EventType, InputEditEventDetails
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
        or (user["role"] != "cc") # allow CC to create events too
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

    # if creator is CC, set state to approved
    if user["role"] == "cc":
        event_instance.status.state = Event_State_Status.approved

    created_id = eventsdb.insert_one(jsonable_encoder(event_instance)).inserted_id
    created_event = Event.parse_obj(eventsdb.find_one({"_id": ObjectId(created_id)}))

    return EventType.from_pydantic(created_event)


@strawberry.mutation
def editEvent(details: InputEditEventDetails, info: Info) -> EventType:
    """
    edit event with given details if user has permission
    return the event
    """
    user = info.context.user

    updates = {
        "status.state": Event_State_Status.incomplete,
    }

    if details.name is not None:
        updates["name"] = details.name
    if details.datetimeperiod is not None:
        updates["datetimeperiod"] = details.datetimeperiod
    if details.mode is not None:
        updates["mode"] = Event_Mode(details.mode)
    if details.location is not None:
        updates["status.room"] = False
        updates["location"] = [Event_Location(loc) for loc in details.location]
    if details.description is not None:
        updates["description"] = details.description
    if details.poster is not None:
        updates["poster"] = details.poster
    if details.audience is not None:
        updates["audience"] = [Audience(aud) for aud in details.audience]
    if details.link is not None:
        updates["link"] = details.link
    if details.equipment is not None:
        updates["equipment"] = details.equipment
    if details.additional is not None:
        updates["additional"] = details.additional
    if details.population is not None:
        updates["population"] = details.population
    if details.budget is not None:
        updates["status.budget"] = False
        updates["budget"] = details.budget

    query = {
        "_id": ObjectId(details.eventid),
        "clubid": user["uid"] if (user is not None and user["role"] == "club") else details.clubid if (user["role"] == "cc") else None,
    }

    updation = {"$set": updates}

    upd_ref = eventsdb.update_one(query, updation)
    if upd_ref.matched_count == 0:
        raise Exception("You do not have permission to access this resource.")

    event_ref = eventsdb.find_one({"_id": ObjectId(details.eventid)})
    return EventType.from_pydantic(Event.parse_obj(event_ref))


@strawberry.mutation
def progressEvent(
    eventid: str,
    info: Info,
    cc_progress_budget: bool | None = None,
    cc_progress_room: bool | None = None,
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
            "budget": event_instance.status.budget or sum([b.amount for b in event_instance.budget]) == 0,
            "room": event_instance.status.room or len(event_instance.location) == 0,
            "state": Event_State_Status.pending_cc.value,
        }

    elif event_instance.status.state == Event_State_Status.pending_cc:
        if user["role"] != "cc":
            raise noaccess_error
        updation = {
            "budget": event_instance.status.budget or sum([b.amount for b in event_instance.budget]) == 0,
            "room": event_instance.status.room or len(event_instance.location) == 0,
        }
        if cc_progress_budget is not None:
            updation["budget"] = cc_progress_budget
        if cc_progress_room is not None:
            updation["room"] = cc_progress_room

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

    upd_ref = eventsdb.update_one({"_id": ObjectId(eventid)}, {"$set": {"status": updation}})
    if upd_ref.matched_count == 0:
        raise noaccess_error

    event_ref = eventsdb.find_one({"_id": ObjectId(eventid)})
    return EventType.from_pydantic(Event.parse_obj(event_ref))


@strawberry.mutation
def deleteEvent(eventid: str, info: Info) -> EventType:
    """
    change the state of the event to `deleted` if the user has permissions
    """
    user = info.context.user

    query = {
        "_id": ObjectId(eventid),
    }
    if user["role"] not in ["cc"]:
        # if user is not an admin, they can only delete their own events
        query["clubid"] = user["uid"]

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
    editEvent,
    progressEvent,
    deleteEvent,
]
