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
    HttpUrlString,
    PrizesType,
    PyObjectId,
    event_popu_type,
    long_str_type,
    medium_str_type,
    short_str_type,
    timezone,
    very_short_str_type,
)


class EventReport(BaseModel):
    eventid: str
    summary: medium_str_type
    attendance: event_popu_type
    prizes: List[PrizesType] = []
    prizes_breakdown: long_str_type
    winners: long_str_type
    photos_link: HttpUrlString
    feedback_cc: medium_str_type
    feedback_college: medium_str_type
    submitted_by: str
    submitted_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone), frozen=True
    )


class Event(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    code: str | None = None
    clubid: str
    collabclubs: List[str] = []
    studentBodyEvent: bool = False

    name: very_short_str_type

    description: medium_str_type | None = "No description available."
    datetimeperiod: Tuple[datetime, datetime]
    poster: str | None = None
    audience: List[Audience] = []
    link: HttpUrlString | None = None

    mode: Event_Mode = Event_Mode.hybrid
    location: List[Event_Location] = []
    equipment: short_str_type | None = None
    additional: short_str_type | None = None
    population: event_popu_type | None = None
    poc: str | None = None

    status: Event_Status = Event_Status()
    budget: List[BudgetType] = []
    bills_status: Bills_Status = Bills_Status()
    event_report_submitted: bool = False

    @field_validator("datetimeperiod")
    def check_end_year(cls, value, info: ValidationInfo):
        if value[0] >= value[1]:
            raise ValueError("Start date cannot be same/after end date")
        return value

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="forbid",
        str_strip_whitespace=True,
    )


class Holiday(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: very_short_str_type
    date: date
    description: medium_str_type | None = None
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
