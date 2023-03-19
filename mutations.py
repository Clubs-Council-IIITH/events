import strawberry

from fastapi.encoders import jsonable_encoder

from db import eventsdb

# import all models and types
from models import Event
from otypes import Info, InputEventDetails, EventType
from mtypes import Event_Mode, Event_Location, Audience, Event_State


@strawberry.mutation
def createEvent (details: InputEventDetails, info: Info) -> EventType :
    '''
        create event with given details if user has permission
        return the event
    '''
    user = info.context.user

    user = dict() # TODO : remove after testing
    user.update({ "clubs": ["2"], "role": None }) # TODO : remove after testing

    if not user or not details.clubid or details.clubid not in user["clubs"] :
       raise Exception(
           "You do not have permission to access this resource."
       )

    event_instance = Event(
        name = details.name,
        clubid = details.clubid,
        datetimeperiod = details.datetimeperiod,
    )
    if details.mode is not None :
        event_instance.mode = Event_Mode(details.mode)
    if details.location is not None :
        event_instance.location = [ Event_Location(loc) for loc in details.location ]
    if details.description is not None :
        event_instance.description = details.description
    if details.poster is not None :
        event_instance.poster = details.poster
    if details.audience is not None :
        event_instance.audience = [ Audience(aud) for aud in details.audience ]
    if details.link is not None :
        event_instance.link = details.link
    if details.equipment is not None :
        event_instance.equipment = details.equipment
    if details.additional is not None :
        event_instance.additional = details.additional
    if details.population is not None :
        event_instance.population = details.population

    created_id = eventsdb.insert_one(jsonable_encoder(event_instance)).inserted_id
    created_event = Event.parse_obj(eventsdb.find_one({"_id": created_id}))

    return EventType.from_pydantic(created_event)

@strawberry.mutation
def progressEvent (eventid: str, info: Info, cc_progress_budget: bool = False, cc_progress_room: bool = False) -> EventType :
    '''
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
    '''
    # TODO : consider using replace_one instead of find_one and save
    noaccess_error = Exception("Can not access event. Either it does not exist or user does not have perms.")

    user = info.context.user

    user = dict() # TODO : remove after testing
    user.update({ "clubs": ["2"], "role": None }) # TODO : remove after testing

    event_instance = eventsdb.find_one({"_id": eventid})
    if event_instance is None or user is None :
        raise noaccess_error

    if event_instance.status.state == Event_State.incomplete :
        if event_instance.clubid not in user["clubs"] :
            raise noaccess_error
        event_instance.status.budget_approved = False
        event_instance.status.room_approved = False
        event_instance.status.state = Event_State.cc_pending

    elif event_instance.status.state == Event_State.cc_pending :
        if user["role"] != "cc" :
            raise noaccess_error
        event_instance.status.budget_approved = cc_progress_budget or sum([b.amount for b in event_instance.budget]) == 0
        event_instance.status.room_approved = cc_progress_room or len(event_instance.location) == 0

        if not event_instance.status.budget_approved :
            event_instance.status.state = Event_State.budget_pending
        elif not event_instance.status.room_approved :
            event_instance.status.state = Event_State.room_pending
        else :
            event_instance.status.state = Event_State.approved

    elif event_instance.status.state == Event_State.budget_pending :
        if user["role"] != "slc" :
            raise noaccess_error
        assert(event_instance.status.budget_approved == False)
        event_instance.status.budget_approved = True
        event_instance.status.room_approved |= len(event_instance.location) == 0

        if not event_instance.status.room_approved :
            event_instance.status.state = Event_State.room_pending
        else :
            event_instance.status.state = Event_State.approved
            
    elif event_instance.status.state == Event_State.room_pending :
        if user["role"] != "slo" :
            raise noaccess_error
        assert(event_instance.status.budget_approved == True)
        assert(event_instance.status.room_approved == False)
        event_instance.status.room_approved = True

        event_instance.status.state = Event_State.approved
    
    elif event_instance.status.state == Event_State.approved :
        if user["role"] != "cc" or event_instance.clubid not in user["clubs"] :
            raise noaccess_error

        event_instance.status.state = Event_State.completed
        
    event_instance.save()
    return EventType.from_pydantic(event_instance)

@strawberry.mutation
def deleteEvent (eventid: str, info: Info) -> EventType :
    '''
        change the state of the event to `deleted` if the user has permissions
    '''
    user = info.context.user

    user = dict() # TODO : remove after testing
    user.update({ "clubs": ["2"], "role": None }) # TODO : remove after testing
    
    if user["role"] in ["cc",] :
        query = {
            "_id": eventid,
        }
    else :
        query = {
            "_id": eventid,
            "clubid": {"$in": user["clubs"]},
        }

    replacement = {"status": {
        "state": Event_State.deleted,
        "budget_approved": False,
        "room_approved": False,
    }}

    event_instance = eventsdb.replace_one(query,replacement)
    return event_instance


# register all mutations
mutations = [
    createEvent,
    progressEvent,
    deleteEvent,
]
