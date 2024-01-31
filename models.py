from bson import ObjectId
from datetime import datetime
from typing import Tuple, List
from pydantic import (
    ConfigDict, 
    field_validator,
    BaseModel, 
    Field, 
    HttpUrl,
    ValidationInfo
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
    datetimeperiod: Tuple[datetime, datetime]
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

    @field_validator("datetimeperiod")
    def check_end_year(cls, value, info: ValidationInfo):
        if value[0] >= value[1]:
            raise ValueError("Start date cannot be same/after end date")
        return value
    
    # TODO[pydantic]: The following keys were removed: `json_encoders`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, json_encoders={ObjectId: str})
