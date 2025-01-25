import json
from datetime import date, datetime
from functools import cached_property
from typing import Dict, List, Tuple, TypeAlias

import strawberry
from pydantic import BaseModel
from strawberry.fastapi import BaseContext
from strawberry.types import Info as _Info
from strawberry.types.info import RootValueType

from models import Event, EventReport, Holiday
from mtypes import (
    Audience,
    Bills_State_Status,
    Bills_Status,
    BudgetType,
    Event_Location,
    Event_Mode,
    PyObjectId,
)


# custom context class
class Context(BaseContext):
    """
    Class provides user metadata and cookies from request headers, has
    methods for doing this.
    """

    @cached_property
    def user(self) -> Dict | None:
        if not self.request:
            return None
        user = json.loads(self.request.headers.get("user", "{}"))
        return user

    @cached_property
    def cookies(self) -> Dict | None:
        if not self.request:
            return None

        cookies = json.loads(self.request.headers.get("cookies", "{}"))
        return cookies


# custom info type
Info: TypeAlias = _Info[Context, RootValueType]

# serialize PyObjectId as a scalar type
PyObjectIdType = strawberry.scalar(
    PyObjectId, serialize=str, parse_value=lambda v: PyObjectId(v)
)


@strawberry.experimental.pydantic.type(model=EventReport, all_fields=True)
class EventReportType:
    """
    Type for returning the event's report.
    """
    pass


@strawberry.experimental.pydantic.type(model=Event, all_fields=True)
class EventType:
    """
    Type for returning all the details regarding an event.
    """

    pass


class RoomList(BaseModel):
    """
    Model for storing the list of rooms.
    """

    locations: List[Event_Location]


@strawberry.experimental.pydantic.type(model=RoomList, all_fields=True)
class RoomListType:
    """
    Type for returning a list of locations.
    """

    pass


@strawberry.type
class BillsStatusType:
    """
    Type for returning event id, event name, club id and bills status of
    the event.
    """

    eventid: str
    eventname: str
    clubid: str
    bills_status: Bills_Status
    eventReportSubmitted: str


@strawberry.input
class InputBillsStatus:
    """
    Input for taking event id, state of the bill and slo comment during
    the approval/rejection of bills.
    """

    eventid: str
    state: Bills_State_Status
    slo_comment: str | None = None


@strawberry.input
class BudgetInput(BudgetType):
    """
    Input for taking all fields of the BudgetType class.
    """

    pass


@strawberry.input
class InputEventDetails:
    """
    Class for taking the details of an event.

    Attributes:
        name (str): Name of the event.
        location (List[Event_Location]): List of locations of the event. 
                                         Default is None.
        description (str): Description of the event. Default is None.
        clubid (str): clubID of the club organizing the event.
        collabclubs (List[str]): List of clubIDs of collaborating clubs.
                                 Default is None.
        mode (Event_Mode): Mode of the event. Default is hybrid.
        poster (str): Poster of the event. Default is None.
        datetimeperiod (List[datetime]): List of date and time of start and 
                                         end of the event.
        audience (List[Audience]): List of audience categories for the event.
                                   Default is None.
        link (str): Link to the event. Default is None.
        equipment (str): Equipment for the event. Default is None.
        additional (str): Additional information of the event.
                          Default is None.
        population (int): Population expected to attend the event.
                          Default is None.
        budget (List[BudgetInput]): List of budgets of the event.
                                    Default is None.
        poc (str): Point of contact for the event.
    """

    name: str
    location: List[Event_Location] | None = None
    description: str | None = None
    clubid: str
    collabclubs: List[str] | None = None
    mode: Event_Mode | None = Event_Mode.hybrid
    poster: str | None = None
    datetimeperiod: List[datetime]
    audience: List[Audience] | None = None
    link: str | None = None
    equipment: str | None = None
    additional: str | None = None
    population: int | None = None
    budget: List[BudgetInput] | None = None
    poc: str


@strawberry.input
class InputEditEventDetails:
    """
    Input similar to InputEventDetails but along with the event 
    id(self-generated) attribute.
    """

    name: str | None = None
    eventid: str
    collabclubs: List[str] | None = None
    location: List[Event_Location] | None = None
    description: str | None = None
    clubid: str | None
    mode: Event_Mode | None = Event_Mode.hybrid
    poster: str | None = None
    datetimeperiod: List[datetime] | None = None
    audience: List[Audience] | None = None
    link: str | None = None
    equipment: str | None = None
    additional: str | None = None
    population: int | None = None
    budget: List[BudgetInput] | None = None
    poc: str | None = None


@strawberry.input
class InputDataReportDetails:
    """
    Input used for taking info required to bring a list of events along 
    with required fields.
    """

    clubid: str | None
    dateperiod: List[date] | None = None
    fields: List[str]
    status: str


@strawberry.experimental.pydantic.input(model=EventReport, all_fields=True)
class InputEventReport:
    """
    Input for taking all the fields of the EventReport model.
    """
    pass


@strawberry.type
class CSVResponse:
    """
    Type for returning the csv file, success/error message.
    """

    csvFile: str
    successMessage: str
    errorMessage: str


# custom data type for start and end of event
timelot_type = Tuple[datetime, datetime]

# Holidays Types


@strawberry.input
class InputHolidayDetails:
    """
    Input for taking the details of a holiday.
    """

    date: date
    name: str
    description: str | None = None


@strawberry.experimental.pydantic.type(model=Holiday, all_fields=True)
class HolidayType:
    """
    Type for returning all the details regarding a holiday.
    """

    pass
