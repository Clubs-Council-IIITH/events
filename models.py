from bson import ObjectId
from .types import (
    Audience,
    Event_Status,
    event_name_type,
    event_desc_type,
    event_popu_type,
    event_othr_type,
    Event_Mode,
    Event_Location,
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
)

# for handling mongo ObjectIds
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


# sample pydantic model
class Sample(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    name: event_name_type
    location: Event_Location = Event_Location._none
    status: Event_Status = Event_Status()
    description: event_desc_type | None = None # todo(FE): if None, use "No description available."
    club: PyObjectId
    mode: Event_Mode
    poster: FilePath | None = None # todo: upload_to="imgs/events/"; todo(FE): if None, use default
    datetimeperiod: Tuple[datetime, datetime]
    audience: Audience = Audience._all
    link: HttpUrl | None = None
    equipment: event_othr_type | None = None
    additional: event_othr_type | None = None
    population: event_popu_type | None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
