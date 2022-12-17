import strawberry

from fastapi.encoders import jsonable_encoder

from db import db

# import all models and types
from models import Sample
from otypes import SampleMutationInput, SampleType


# sample mutation
@strawberry.mutation
def sampleMutation(sampleInput: SampleMutationInput) -> SampleType:
    sample = jsonable_encoder(sampleInput.to_pydantic())

    # add to database
    created_id = db.samples.insert_one(sample).inserted_id

    # query from database
    created_sample = Sample.parse_obj(db.samples.find_one({"_id": created_id}))

    return SampleType.from_pydantic(created_sample)
