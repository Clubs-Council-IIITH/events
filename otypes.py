import json
import strawberry

from strawberry.fastapi import BaseContext
from strawberry.types import Info as _Info
from strawberry.types.info import RootValueType

from typing import Dict, List
from functools import cached_property
from datetime import datetime

from models import Event
from mtypes import PyObjectId

# custom context class
class Context(BaseContext):
    @cached_property
    def user(self) -> Dict | None :
        if not self.request:
            return None
        user = json.loads(self.request.headers.get("user", "{}"))
        return user

# custom info type
Info = _Info[Context, RootValueType]

# serialize PyObjectId as a scalar type
PyObjectIdType = strawberry.scalar(
    PyObjectId, serialize=str, parse_value=lambda v: PyObjectId(v)
)

@strawberry.experimental.pydantic.type(model=Event, all_fields=True)
class EventType :
    pass

@strawberry.input()
class InputEventDetails :
    name: str
    location: List[int] | None = None
    description: str | None = None
    clubid: str
    mode: int | None = 1
    poster: str | None = None
    datetimeperiod: List[datetime]
    audience: List[int] | None = None
    link: str | None = None
    equipment: str | None = None
    additional: str | None = None
    population: str | None = None