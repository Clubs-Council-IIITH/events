import strawberry

from pydantic import BaseModel, Field

from models import PyObjectId, Sample


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
