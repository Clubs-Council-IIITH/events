import strawberry
from fastapi.encoders import jsonable_encoder

from db import holidaysdb
from models import Holiday
from otypes import HolidayType, Info, InputHolidayDetails


@strawberry.mutation
def createHoliday(details: InputHolidayDetails, info: Info) -> HolidayType:
    """
    Create a new holiday
    returns the created holiday

    Allowed Roles: ["slo"]
    """
    user = info.context.user

    if user is None or user.get("role") not in ["slo"]:
        raise ValueError("You do not have permission to access this resource.")

    holiday = Holiday(
        name=details.name,
        date=details.date,
        description=details.description,
    )

    # Check if any holiday on that day already exists
    if holidaysdb.find_one({"date": str(details.date)}):
        raise ValueError("A holiday already exists on this day.")

    created_id = holidaysdb.insert_one(jsonable_encoder(holiday)).inserted_id
    created_holiday = holidaysdb.find_one({"_id": created_id})

    return HolidayType.from_pydantic(Holiday.parse_obj(created_holiday))


@strawberry.mutation
def editHoliday(
    id: str, details: InputHolidayDetails, info: Info
) -> HolidayType:
    """
    Edit an existing holiday
    returns the edited holiday

    Allowed Roles: ["slo"]
    """
    user = info.context.user

    if user is None or user.get("role") not in ["slo"]:
        raise ValueError("You do not have permission to access this resource.")

    holiday = holidaysdb.find_one({"_id": id})
    if holiday is None:
        raise ValueError("Holiday not found.")

    # Check if any other holiday on that day already exists
    if holidaysdb.find_one({"date": str(details.date), "_id": {"$ne": id}}):
        raise ValueError("A holiday already exists on this day.")

    holidaysdb.find_one_and_update(
        {"_id": id}, {"$set": jsonable_encoder(details)}
    )
    updated_holiday = holidaysdb.find_one({"_id": id})

    return HolidayType.from_pydantic(Holiday.parse_obj(updated_holiday))


@strawberry.mutation
def deleteHoliday(id: str, info: Info) -> bool:
    """
    Delete an existing holiday
    returns a boolean indicating success

    Allowed Roles: ["slo"]
    """
    user = info.context.user

    if user is None or user.get("role") not in ["slo"]:
        raise ValueError("You do not have permission to access this resource.")

    holiday = holidaysdb.find_one({"_id": id})
    if holiday is None:
        raise ValueError("Holiday not found.")

    holidaysdb.delete_one({"_id": id})

    return True


# register all mutations of holidays
mutations = [
    createHoliday,
    editHoliday,
    deleteHoliday,
]
