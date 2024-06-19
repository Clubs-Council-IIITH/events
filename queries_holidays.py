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
        query["date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["date"] = {"$gte": start_date}
    elif end_date:
        query["date"] = {"$lte": end_date}

    holidays = holidaysdb.find(query)

    return [
        HolidayType.from_pydantic(Holiday.parse_obj(holiday))
        for holiday in holidays
    ]


# register all queries of holidays
queries = [
    holidays,
]
