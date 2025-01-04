"""
Mutation Resolvers for Holidays

Contains mutation resolvers for creating, updating, and deleting holidays.
"""

import strawberry
from fastapi.encoders import jsonable_encoder

from db import holidaysdb
from models import Holiday
from otypes import HolidayType, Info, InputHolidayDetails


@strawberry.mutation
def createHoliday(details: InputHolidayDetails, info: Info) -> HolidayType:
    """
    Create a new holiday
    
    This method creates a new holiday in the database.

    Inputs:
        details (InputHolidayDetails): The details of the holiday to be created.
        info (Info): The context of the request for user info.

    Returns:
        HolidayType: The created holiday.

    Accessibility:
        Accessible to slo and cc.

    Raises Exception:
        Not Authenticated: If the user is not authenticated or if user is not logged in.
        Holiday already exists: If a holiday already exists on the given date.
    """
    user = info.context.user

    if user is None or user.get("role") not in ["slo", "cc"]:
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

    return HolidayType.from_pydantic(Holiday.model_validate(created_holiday))


@strawberry.mutation
def editHoliday(
    id: str, details: InputHolidayDetails, info: Info
) -> HolidayType:
    """
    Edit an existing holiday
    
    This method edits an existing holiday in the database.

    Inputs:
        id (str): The id of the holiday to be edited.
        details (InputHolidayDetails): The details to which the holiday is to be updated.
        info (Info): The context of the request for user info.

    Returns:
        HolidayType: The edited holiday.

    Accessibility:
        Accessible to slo and cc.

    Raises Exception:
        Not Authenticated: If the user is not authenticated or if user is not logged in.
        Holiday not found: If a holiday with the given id does not exist in the database.
        Holiday already exists: If a holiday already exists on the given date to which the holiday is to be updated.
    """
    user = info.context.user

    if user is None or user.get("role") not in ["slo", "cc"]:
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

    return HolidayType.from_pydantic(Holiday.model_validate(updated_holiday))


@strawberry.mutation
def deleteHoliday(id: str, info: Info) -> bool:
    """
    Delete an existing holiday
    
    This method deletes an existing holiday in the database.

    Inputs:
        id (str): The id of the holiday to be deleted.
        info (Info): The context of the request for user info.

    Returns:
        bool: True if the holiday was deleted successfully, False otherwise.

    Accessibility:
        Accessible to slo and cc.

    Raises Exception:
        Not Authenticated: If the user is not authenticated or if user is not logged in.
        Holiday not found: If a holiday with the given id does not exist in the database.
    """
    user = info.context.user

    if user is None or user.get("role") not in ["slo", "cc"]:
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
