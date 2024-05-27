from bson import ObjectId
from datetime import datetime, timedelta
from typing import List
from typing_extensions import Self
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

    @field_validator('duration')
    def check_duration(cls, value: str, info: ValidationInfo):
        hours, minutes = value.split(':')
        time_obj = timedelta(hours=int(hours),minutes=int(minutes))
        five_mins = timedelta(hours=0, minutes=5)
        assert time_obj > five_mins, "The duration of event should be larger than 5 minutes"
        return value

    @model_validator(mode='after')
    def checkdates(self) -> Self:
        start_str = self.start_time
        end_str = self.end_time
        start_time_obj = datetime.strptime(start_str, "%d-%m-%Y %H:%M")
        end_time_obj = datetime.strptime(end_str, "%d-%m-%Y %H:%M")

        duration_str = self.duration
        hours, minutes = duration_str.split(':')
        duration_obj = timedelta(hours=int(hours), minutes=int(minutes))

        if start_time_obj >= end_time_obj:
            raise ValueError("The start time should be before the end time")
        
        if (start_time_obj + duration_obj) != end_time_obj:
            raise ValueError("The duration is not matching with start and end times")

        return self

    # TODO[pydantic]: The following keys were removed: `json_encoders`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )
