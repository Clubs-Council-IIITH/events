import json
import strawberry

from strawberry.fastapi import BaseContext
from strawberry.types import Info as _Info
from strawberry.types.info import RootValueType

from typing import Dict, Tuple
from functools import cached_property

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

# object type from pydantic model with all fields exposed
@strawberry.experimental.pydantic.type(model=Event, all_fields=True)
class EventType :
    pass

# mutation's input type from pydantic model
@strawberry.experimental.pydantic.input(model=Event)
class InputEventDetails :
    name: strawberry.auto
    location: strawberry.auto
    description: strawberry.auto
    clubid: strawberry.auto
    modeNum: int
    poster: strawberry.auto
    datetimeperiod: strawberry.auto
    audience: strawberry.auto
    link: strawberry.auto
    equipment: strawberry.auto
    additional: strawberry.auto
    population: strawberry.auto