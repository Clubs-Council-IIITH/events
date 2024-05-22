from bson import ObjectId
from datetime import datetime, timedelta
from typing import Tuple, List
from pydantic import (
    ConfigDict,
    field_validator,
    model_validator,
    BaseModel,
    Field,
    HttpUrl,
    ValidationInfo,
)

from mtypes import (
    Audience,
    BudgetType,
    Event_Status,
    event_name_type,
    event_desc_type,
    event_popu_type,
    event_othr_type,
    Event_Mode,
    Event_Location,
    PyObjectId,
)


class Event(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    code: str | None = None
    name: event_name_type
    clubid: str
    start_time: str
    end_time: str
    duration: str
    status: Event_Status = Event_Status()
    location: List[Event_Location] = []
    description: event_desc_type | None = "No description available."
    mode: Event_Mode = Event_Mode.hybrid
    poster: str | None = None
    audience: List[Audience] = []
    link: HttpUrl | None = None
    equipment: event_othr_type | None = None
    additional: event_othr_type | None = None
    population: event_popu_type | None = None
    budget: List[BudgetType] = []
    poc: str | None = None

    #@field_validator('duration')
    #def check_duration(cls, value, info: ValidationInfo):
    #    time_obj = time.strptime(value, "%H-%M")
    #    five_mins = time(0, 5)
    #    assert time_obj > five_mins, "The duration of event should be larger than 5 minutes"
    #    return value

    #@model_validator(mode='after')
    #def checkdates(cls, values, info: ValidationInfo):
    #    start_str = values.get('start_time')
    #    end_str = values.get('end_time')
    #    start_time_obj = datetime.strptime(start_str, "%d-%m-%Y %H:%M")
    #    end_time_obj = datetime.strptime(end_str, "%d-%m-%Y %H:%M")

    #    duration_str = values.get('duration')
    #    hours, minutes = duration_str.split(':')
    #    duration_obj = timedelta.strptime(hours, minutes)

    #    validity =  start_time_obj < end_time_obj
    #    assert validity, "The start time should be before end time"

    #    duration_validity = ((start_time_obj + duration_obj) == end_time_obj)
    #    assert duration_validity, "The duration is not matching with start and end times"

    #    return values

    # TODO[pydantic]: The following keys were removed: `json_encoders`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )
