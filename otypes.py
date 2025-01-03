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
