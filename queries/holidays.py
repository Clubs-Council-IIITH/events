"""
Query Resolvers for holidays
"""

from datetime import date
from typing import List

import strawberry

from db import holidaysdb
from models import Holiday
from otypes import HolidayType


@strawberry.field
async def holidays(
    start_date: date | None = None, end_date: date | None = None
) -> List[HolidayType]:
    """
    Get a list of holidays from a start date(if provided) to an end date
    (if provided).

    Args:
        start_date (date, optional): The start date of the range. Defaults to
                                     None.
        end_date (date, optional): The end date of the range.
                                   Defaults to None.

    Returns:
        (List[HolidayType]): A list of holidays.

    Raises:
        ValueError: Start date cannot be greater than end date.
    """

    query = {}
    if start_date and end_date:
        if start_date > end_date:
            raise ValueError("Start date cannot be greater than end date.")
        query["date"] = {"$gte": str(start_date), "$lte": str(end_date)}
    elif start_date:
        query["date"] = {"$gte": str(start_date)}
    elif end_date:
        query["date"] = {"$lte": str(end_date)}

    holidays = await holidaysdb.find(query).to_list(length=None)
    return [
        HolidayType.from_pydantic(Holiday.model_validate(holiday))
        for holiday in holidays
    ]


@strawberry.field
async def holiday(id: str) -> HolidayType:
    """
    This method searches for a holiday by its id and returns it.

    Args:
        id (str): The id of the holiday.

    Returns:
        (HolidayType): The holiday's details.
    """

    holiday = await holidaysdb.find_one({"_id": id})

    return HolidayType.from_pydantic(Holiday.model_validate(holiday))


# register all queries of holidays
queries = [
    holidays,
    holiday,
]
