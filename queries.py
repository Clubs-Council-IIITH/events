import strawberry

from fastapi.encoders import jsonable_encoder

from db import db

# import all models and types
from models import Sample
from otypes import Info, SampleQueryInput, SampleType


# sample query
@strawberry.field
def sampleQuery(sampleInput: SampleQueryInput, info: Info) -> SampleType:
    user = info.context.user
    print("user:", user)

    sample = jsonable_encoder(sampleInput.to_pydantic())

    # query from database
    found_sample = db.samples.find_one({"_id": sample["_id"]})

    # handle missing sample
    if found_sample:
        found_sample = Sample.parse_obj(found_sample)
        return SampleType.from_pydantic(found_sample)

    else:
        raise Exception("Sample not found!")


# register all queries
queries = [
    sampleQuery,
]
