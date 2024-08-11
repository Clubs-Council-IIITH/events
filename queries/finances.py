from datetime import datetime
from typing import List

import strawberry

from db import eventsdb
from mtypes import Bills_Status, Event_State_Status
from otypes import BillsStatusType, Info


@strawberry.field
def eventBills(eventid: str, info: Info) -> Bills_Status:
    """
    Get the bills status of an event
    returns the bills status
    """

    user = info.context.user
    if not user:
        raise ValueError("User not authenticated")
    
    user_role = user["role"]
    if user_role not in ["cc", "slo", "club"]:
        raise ValueError("User not authorized")
    
    searchspace = {
        "_id": eventid,
        "status.state": Event_State_Status.approved.value,  # type: ignore
        "datetimeperiod.1": {
            "$lt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        },
        "budget": {
            "$exists": True,
            "$ne": [],
        },  # Ensure the budget array exists and is not empty
    }

    if user_role == "club":
        searchspace.update({"clubid": user["uid"]})

    event = eventsdb.find_one(searchspace)

    if not event:
        raise ValueError("Event not found")

    if "bills_status" not in event:
        raise ValueError("Bills status not found")

    return Bills_Status(**event["bills_status"])


@strawberry.field
def allEventsBills(info: Info) -> List[BillsStatusType]:
    """
    Get the bills status of an event
    returns the bills status
    """

    user = info.context.user
    if not user:
        raise ValueError("User not authenticated")

    user_role = user["role"]
    if user_role not in ["club", "cc", "slo"]:
        raise ValueError("User not authorized")

    searchspace = {
        "status.state": Event_State_Status.approved.value,  # type: ignore
        "datetimeperiod.1": {
            "$lt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        },
        "bills_status": {"$exists": True},
        "budget": {
            "$exists": True,
            "$ne": [],
        },  # Ensure the budget array exists and is not empty
    }

    if user_role == "club":
        searchspace.update({"clubid": user["uid"]})
    events = list(eventsdb.find(searchspace).sort("datetimeperiod.1", -1))

    if not events or len(events) == 0:
        raise ValueError("No events found")

    return [
        BillsStatusType(
            eventid=event["_id"],
            eventname=event["name"],
            clubid=event["clubid"],
            bills_status=Bills_Status(**event["bills_status"]),
        )
        for event in events
    ]


# register all queries for finances
queries = [eventBills, allEventsBills]
