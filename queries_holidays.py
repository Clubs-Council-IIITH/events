from datetime import date
from typing import List

import strawberry

from db import holidaysdb
from models import Holiday
from otypes import HolidayType


@strawberry.field
def holidays(
    start_date: date | None = None, end_date: date | None = None
) -> List[HolidayType]:
    """
    Get all holidays
    returns all holidays
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

    holidays = holidaysdb.find(query)

    return [
        HolidayType.from_pydantic(Holiday.parse_obj(holiday))
        for holiday in holidays
    ]


# register all queries of holidays
queries = [
    holidays,
]
