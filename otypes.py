"""
Types and Inputs

This file coniains all the types and inputs that we will be using in the events module.
It also contais a model RoomList which is used to store the list of rooms.
Even holidays are also stored as events.

Types:
    Info: used to return user and cookes details.
    PyObjectIdType : used to return the ObjectId as a string.
    EventType : used to return all the details regarding an event.
    RoomListType : used to return a list of location(RoomList).
    BillsStatusType : used to return event id, event name, club id and bills status of the club.
    CSVResponse : used to return a csvFile and its success and error messages.
    HolidayType : used to return all the fields within the Holiday class.

Inputs:
    InputBillsStatus : used to input event id, state of the bill and slo comment during the approval of bills.
    BudgetInput : used to input all fields of the BudgetType class.
    InputEventDetails : used to input all fields of the InputEventDetails class that should be filled by the organizing club.
    InputEventEditDetails : used to input all fields of the InputEventDetails along with the event id.
    InputDataReportDetails : used in the CSVResponse method to bring to bring in all the list of events accroding to the fields within this Input class.
    InputHolidayDetails : used to input name, date and description of a holiday.
"""

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
    pass


@strawberry.experimental.pydantic.type(model=Event, all_fields=True)
class EventType:
    pass


class RoomList(BaseModel):
    locations: List[Event_Location]


@strawberry.experimental.pydantic.type(model=RoomList, all_fields=True)
class RoomListType:
    pass


@strawberry.type
class BillsStatusType:
    eventid: str
    eventname: str
    clubid: str
    bills_status: Bills_Status
    eventReportSubmitted: str


@strawberry.input
class InputBillsStatus:
    eventid: str
    state: Bills_State_Status
    slo_comment: str | None = None


@strawberry.input
class BudgetInput(BudgetType):
    pass


@strawberry.input
class InputEventDetails:
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
    name: str | None = None
    eventid: str
    collabclubs: List[str] | None = None
    location: List[Event_Location] | None = None
    description: str | None = None
    clubid: str | None  # not editable
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
    clubid: str | None
    dateperiod: List[date] | None = None
    fields: List[str]
    status: str


@strawberry.experimental.pydantic.input(model=EventReport, all_fields=True)
class InputEventReport:
    pass


@strawberry.type
class CSVResponse:
    csvFile: str
    successMessage: str
    errorMessage: str

# custom data type for start and end of event
timelot_type = Tuple[datetime, datetime]

# Holidays Types


@strawberry.input
class InputHolidayDetails:
    date: date
    name: str
    description: str | None = None


@strawberry.experimental.pydantic.type(model=Holiday, all_fields=True)
class HolidayType:
    pass
