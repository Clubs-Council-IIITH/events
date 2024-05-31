import json
from datetime import datetime
from functools import cached_property
from typing import Dict, List, Tuple

import strawberry
from pydantic import BaseModel
from strawberry.fastapi import BaseContext
from strawberry.types import Info as _Info
from strawberry.types.info import RootValueType

from models import Event
from mtypes import Audience, BudgetType, Event_Location, Event_Mode, PyObjectId


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
Info = _Info[Context, RootValueType]

# serialize PyObjectId as a scalar type
PyObjectIdType = strawberry.scalar(
    PyObjectId, serialize=str, parse_value=lambda v: PyObjectId(v)
)


@strawberry.experimental.pydantic.type(model=Event, all_fields=True)
class EventType:
    pass


class RoomList(BaseModel):
    locations: List[Event_Location]


@strawberry.experimental.pydantic.type(model=RoomList, all_fields=True)
class RoomListType:
    pass


@strawberry.input()
class BudgetInput(BudgetType):
    pass


@strawberry.input()
class InputEventDetails:
    name: str
    location: List[Event_Location] | None = None
    description: str | None = None
    clubid: str
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


@strawberry.input()
class InputEditEventDetails:
    name: str | None = None
    eventid: str
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


timelot_type = Tuple[datetime, datetime]
