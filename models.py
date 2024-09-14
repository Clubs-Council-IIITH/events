from datetime import date, datetime
from typing import List, Tuple

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    ValidationInfo,
    field_validator,
)

from mtypes import (
    Audience,
    Bills_Status,
    BudgetType,
    Event_Location,
    Event_Mode,
    Event_Status,
    PyObjectId,
    event_desc_type,
    event_name_type,
    event_othr_type,
    event_popu_type,
    timezone,
)


class Event(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    code: str | None = None
    clubid: str
    collabclubs: List[str] = []

    name: event_name_type

    description: event_desc_type | None = "No description available."
    datetimeperiod: Tuple[datetime, datetime]
    poster: str | None = None
    audience: List[Audience] = []
    link: HttpUrl | None = None

    mode: Event_Mode = Event_Mode.hybrid
    location: List[Event_Location] = []
    equipment: event_othr_type | None = None
    additional: event_othr_type | None = None
    population: event_popu_type | None = None
    poc: str | None = None

    status: Event_Status = Event_Status()
    budget: List[BudgetType] = []
    bills_status: Bills_Status = Bills_Status()

    @field_validator("datetimeperiod")
    def check_end_year(cls, value, info: ValidationInfo):
        if value[0] >= value[1]:
            raise ValueError("Start date cannot be same/after end date")
        return value

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class Holiday(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    date: date
    description: str | None = None
    created_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone), frozen=True
    )

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        str_max_length=5000,
        extra="forbid",
        str_strip_whitespace=True,
    )
