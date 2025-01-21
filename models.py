from datetime import date, datetime
from typing import List, Tuple

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
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
    """
    Model for an event's report after completion.
    
    Attributes:
        eventid (str): The ID of the event.
        summary (str): A summary of the event.
        attendance (int): The number of attendees.
        prizes (List[PrizesType]): The list prizes awarded in the event.
        prizes_breakdown (str): A breakdown of the prizes awarded.
        winners (str): The winners of the event.
        photos_link (HttpUrlString): The link to the event's photos.
        feedback_cc (str): Feedback on the event by CC.
        feedback_college (str): Feedback on the event by the college.
        submitted_by (str): The user who submitted the report.
        submitted_time (datetime): The time the report was submitted.
    """
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
    """
    Model for an event.
    
    Attributes:
        id (PyObjectId): The ID of the event's document.
        code (str): The code of the event. Defaults to None.
        clubid (str): The Club ID of the club hosting the event.
        collabclubs (List[str]): The Club IDs of the collaborating clubs.
        studentBodyEvent (bool): Whether the event is a student body event. Defaults to False.
        name (very_short_str_type): The name of the event.
        description (medium_str_type): A description of the event. Defaults to "No description available.".
        datetimeperiod (Tuple[datetime, datetime]): The start and end times of the event.
        poster (str): The URL of the event's poster. Defaults to None.
        audience (List[Audience]): The list audience for the event.
        link (HttpUrlString): The link to the event's page. Defaults to None.
        mode (Event_Mode): The mode of the event. Defaults to hybrid.
        location (List[Event_Location]): The list of locations for the event.
        equipment (short_str_type): The equipment required for the event. Defaults to None.
        additional (short_str_type): Additional information about the event. Defaults to None.
        population (event_popu_type): The estimated population for the event. Defaults to None.
        poc (str): The point of contact for the event. Defaults to None.
        status (Event_Status): The approval and approver details.
        budget (List[BudgetInput]): The list of budgets for the event.
        budget_status (Bills_Status): The status of the budget.
        event_report_submitted (bool): Whether the event report after completion has been submitted. Defaults to False.
    """
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
    """
    Model for a holiday.
    
    Attributes:
        id (PyObjectId): The ID of the holiday's document.
        name (very_short_str_type): The name of the holiday.
        date (date): The date of the holiday.
        description (medium_str_type): A description of the holiday. Defaults to None.
        created_time (datetime): The time the holiday was created.
    """
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
