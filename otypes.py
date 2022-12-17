import strawberry

from models import Sample


# sample object type from pydantic model with all fields exposed
@strawberry.experimental.pydantic.type(model=Sample, all_fields=True)
class SampleType:
    pass


# sample input type from pydantic model
@strawberry.experimental.pydantic.input(model=Sample)
class SampleInput:
    attribute: strawberry.auto
