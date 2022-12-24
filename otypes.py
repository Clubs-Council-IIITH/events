import json
import strawberry

from strawberry.fastapi import BaseContext
from strawberry.types import Info as _Info
from strawberry.types.info import RootValueType

from typing import Union, Dict
from functools import cached_property

from models import PyObjectId, Sample


# custom context class
class Context(BaseContext):
    @cached_property
    def session(self) -> Union[Dict, None]:
        if not self.request:
            return None

        session = json.loads(self.request.headers.get("session", "{}"))
        return session


# custom info type
Info = _Info[Context, RootValueType]

# serialize PyObjectId as a scalar type
PyObjectIdType = strawberry.scalar(
    PyObjectId, serialize=str, parse_value=lambda v: PyObjectId(v)
)

# sample object type from pydantic model with all fields exposed
@strawberry.experimental.pydantic.type(model=Sample, all_fields=True)
class SampleType:
    pass


# sample query's input type from pydantic model
@strawberry.experimental.pydantic.input(model=Sample)
class SampleQueryInput:
    id: strawberry.auto


# sample mutation's input type from pydantic model
@strawberry.experimental.pydantic.input(model=Sample)
class SampleMutationInput:
    attribute: strawberry.auto
