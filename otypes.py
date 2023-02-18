import json
import strawberry

from strawberry.fastapi import BaseContext
from strawberry.types import Info as _Info
from strawberry.types.info import RootValueType

from typing import Dict
from functools import cached_property

from models import PyObjectId, Event


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

# query's input type from pydantic model
@strawberry.experimental.pydantic.input(model=Event)
class InputEventId :
    id: strawberry.auto

# query's input type from pydantic model
@strawberry.experimental.pydantic.input(model=Event)
class InputClubId :
    clubid: strawberry.auto

# sample mutation's input type from pydantic model
@strawberry.experimental.pydantic.input(model=Event)
class SampleMutationInput:
    attribute: strawberry.auto
