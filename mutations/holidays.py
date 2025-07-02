"""
Mutation Resolvers for Holidays
"""

import strawberry
from fastapi.encoders import jsonable_encoder

from db import holidaysdb
from models import Holiday
from otypes import HolidayType, Info, InputHolidayDetails


@strawberry.mutation
async def createHoliday(details: InputHolidayDetails, info: Info) -> HolidayType:
    """
    Creates a new holiday, for SLO and CC

    Args:
        details (InputHolidayDetails): The details of the holiday to be created.
        info (Info): The context of the request for user info.

    Returns:
        (HolidayType): The created holiday.

    Raises:
        Exception: You do not have permission to access this resource.
        Exception: A holiday already exists on this day.
    """  # noqa: E501
    user = info.context.user

    if user is None or user.get("role") not in ["slo", "cc"]:
        raise ValueError("You do not have permission to access this resource.")

    holiday = Holiday(
        name=details.name,
        date=details.date,
        description=details.description,
    )

    # Check if any holiday on that day already exists
    if await holidaysdb.find_one({"date": str(details.date)}):
        raise ValueError("A holiday already exists on this day.")

    created_id = (await holidaysdb.insert_one(jsonable_encoder(holiday))).inserted_id
    created_holiday = await holidaysdb.find_one({"_id": created_id})

    return HolidayType.from_pydantic(Holiday.model_validate(created_holiday))


@strawberry.mutation
async def editHoliday(
    id: str, details: InputHolidayDetails, info: Info
) -> HolidayType:
    """
    Edit an existing holiday, for SLO and CC

    Args:
        id (str): The id of the holiday to be edited.
        details (InputHolidayDetails): The details to which the holiday is to be updated.
        info (Info): The context of the request for user info.

    Returns:
        (HolidayType): The edited holiday.

    Raises:
        Exception: You do not have permission to access this resource.
        Exception: Holiday not found.
        Exception: A holiday already exists on this day.
    """  # noqa: E501
    user = info.context.user

    if user is None or user.get("role") not in ["slo", "cc"]:
        raise ValueError("You do not have permission to access this resource.")

    holiday = await holidaysdb.find_one({"_id": id})
    if holiday is None:
        raise ValueError("Holiday not found.")

    # Check if any other holiday on that day already exists
    if await holidaysdb.find_one({"date": str(details.date), "_id": {"$ne": id}}):
        raise ValueError("A holiday already exists on this day.")

    await holidaysdb.find_one_and_update(
        {"_id": id}, {"$set": jsonable_encoder(details)}
    )
    updated_holiday = await holidaysdb.find_one({"_id": id})

    return HolidayType.from_pydantic(Holiday.model_validate(updated_holiday))


@strawberry.mutation
async def deleteHoliday(id: str, info: Info) -> bool:
    """
    Delete an existing holiday, for SLO and CC

    Args:
        id (str): The id of the holiday to be deleted.
        info (Info): The context of the request for user info.

    Returns:
        (bool): True if the holiday was deleted successfully, False otherwise.

    Raises:
        Exception: You do not have permission to access this resource.
        Exception: Holiday not found.
    """
    user = info.context.user

    if user is None or user.get("role") not in ["slo", "cc"]:
        raise ValueError("You do not have permission to access this resource.")

    holiday = await holidaysdb.find_one({"_id": id})
    if holiday is None:
        raise ValueError("Holiday not found.")

    await holidaysdb.delete_one({"_id": id})

    return True


# register all mutations of holidays
mutations = [
    createHoliday,
    editHoliday,
    deleteHoliday,
]
