from pydantic import BaseModel


# sample pydantic model
class Sample(BaseModel):
    id: int
    attribute: str
