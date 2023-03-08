import strawberry

from fastapi.encoders import jsonable_encoder

from db import eventsdb

# import all models and types
from models import Event
from otypes import Info, InputEventDetails, EventType
from mtypes import Event_Mode, Event_Location, Audience

@strawberry.mutation
def createEvent (details: InputEventDetails, info: Info) -> EventType :
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


# register all mutations
mutations = [
    createEvent,
]
