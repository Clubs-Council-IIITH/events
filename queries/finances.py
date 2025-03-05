"""
Query Resolvers related to finances
"""

from datetime import datetime
from typing import List

import strawberry

from db import eventsdb
from mtypes import Bills_Status, Event_State_Status
from otypes import BillsStatusType, Info


@strawberry.field
def eventBills(eventid: str, info: Info) -> Bills_Status:
    """
    Get the bills status of an event for cc,slo and club

    Args:
        eventid (str): The id of the event
        info (Info): The user details

    Returns:
        (Bills_Status): The bills status of the event

    Raises:
        ValueError: User not authenticated
        ValueError: User not authorized
        ValueError: Event not found
        ValueError: 'Event' has not ended yet
        ValueError: 'Event' has no budget
        ValueError: 'Event' has no bills status
    """

    user = info.context.user
    if not user:
        raise ValueError("User not authenticated")

    user_role = user["role"]
    if user_role not in ["cc", "slo", "club"]:
        raise ValueError("User not authorized")

    searchspace = {
        "_id": eventid,
        "status.state": Event_State_Status.approved.value,
    }

    if user_role == "club":
        searchspace["$or"] = [  # type: ignore
            {"clubid": user["uid"]},
            {"collabclubs": {"$in": [user["uid"]]}},
        ]

    event = eventsdb.find_one(searchspace)
    if not event:
        raise ValueError(
            "Event not found. Either the event does not exist or you don't have\
                  access to it or it is not approved."
        )

    if event["datetimeperiod"][1] > datetime.now().strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    ):
        raise ValueError(f"{event['name']} has not ended yet.")

    if (
        "budget" not in event
        or not event["budget"]
        or len(event["budget"]) == 0
    ):
        raise ValueError(f"{event['name']} has no budget.")

    if "bills_status" not in event:
        raise ValueError(f"{event['name']} has no bills status.")

    return Bills_Status(**event["bills_status"])
  

@strawberry.field
def allEventsBills(info: Info) -> List[BillsStatusType]:
    """
    Get the bills status of all events
    
    This method is used to fetch the list of bills status of all past 
    approved events that have a budget and bills status.

    Args:
        info (Info): The user details

    Returns:
        (List[BillsStatusType]): The list of bills status of all past approved 
                               events
        
    Raises:
        ValueError: User not authenticated
        ValueError: User not authorized
        ValueError: No events found
    """

    user = info.context.user
    if not user:
        raise ValueError("User not authenticated")

    user_role = user["role"]
    if user_role not in ["club", "cc", "slo"]:
        raise ValueError("User not authorized")

    searchspace = {
        "status.state": Event_State_Status.approved.value,
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
        searchspace.update(
            {
                "$or": [
                    {"clubid": user["uid"]},
                    {"collabclubs": {"$in": [user["uid"]]}},
                ]
            }
        )
    events = list(eventsdb.find(searchspace).sort("datetimeperiod.1", -1))

    if not events or len(events) == 0:
        raise ValueError("No events found")

    return [
        BillsStatusType(
            eventid=event["_id"],
            eventname=event["name"],
            clubid=event["clubid"],
            bills_status=Bills_Status(**event["bills_status"]),
            eventReportSubmitted=event.get("event_report_submitted", "old"),
        )
        for event in events
    ]


# register all queries for finances
queries = [eventBills, allEventsBills]
