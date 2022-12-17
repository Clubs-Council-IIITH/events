from bson import ObjectId
from pydantic import BaseModel, Field

from typing import Optional


# for handling mongo ObjectIds
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


# sample pydantic model
class Sample(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    attribute: Optional[str]

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
