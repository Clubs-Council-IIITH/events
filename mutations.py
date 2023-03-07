import strawberry

from fastapi.encoders import jsonable_encoder

from db import eventsdb

# import all models and types
from models import Event
from otypes import Info, InputEventDetails, EventType
from mtypes import Event_Mode

@strawberry.mutation
def createEvent (eventDetails: InputEventDetails, info: Info) -> EventType :
    modeNum = eventDetails.modeNum
    if not (0 <= modeNum < len(Event_Mode)) :
        raise Exception(
            "Invalid event mode."
        )
    details = eventDetails.to_pydantic()
    details.__class__.mode = Event_Mode(modeNum)

    user = info.context.user

    user = dict() # TODO : remove after testing
    user.update({ "clubs": ["2"], "role": None }) # TODO : remove after testing

    if not user or not details.clubid or details.clubid not in user["clubs"] :
       raise Exception(
           "You do not have permission to access this resource."
       )

    event_instance = Event(
        name =  details.name,
        clubid = details.clubid,
        mode = details.mode,
        datetimeperiod = details.datetimeperiod,
    )
    if details.location is not None :
        event_instance.location = details.location
    if details.description is not None :
        event_instance.description = details.description
    if details.poster is not None :
        event_instance.poster = details.poster # TODO: upload_to="imgs/events/"; TODO (FE): if None, use defaul
    if details.audience is not None :
        event_instance.audience = details.audience
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
