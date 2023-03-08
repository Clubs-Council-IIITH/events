from bson import ObjectId
from mtypes import (
    Audience,
    Event_Status,
    event_name_type,
    event_desc_type,
    event_popu_type,
    event_othr_type,
    Event_Mode,
    Event_Location,
    PyObjectId,
)
from pydantic import (
    BaseModel,
    Field,
    FilePath,
    HttpUrl,
)
from datetime import (
    datetime,
)
from typing import (
    Tuple,
    List,
)

class Event(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: event_name_type
    clubid: str
    datetimeperiod: Tuple[datetime, datetime]
    status: Event_Status = Event_Status()
    location: List[Event_Location] = []
    description: event_desc_type | None = None # todo(FE): if None, use "No description available."
    mode: Event_Mode = Event_Mode.hybrid
    poster: str | None = None
    audience: List[Audience] = []
    link: HttpUrl | None = None
    equipment: event_othr_type | None = None
    additional: event_othr_type | None = None
    population: event_popu_type | None = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
