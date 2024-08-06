from datetime import datetime

import strawberry

from db import eventsdb
from mtypes import (
    Bills_Status,
    Event_State_Status,
    timezone,
)
from otypes import Info, InputBillsStatus


@strawberry.mutation
def updateBillsStatus(details: InputBillsStatus, info: Info) -> Bills_Status:
    """
    Update the bills status of an event
    returns the updated bills status

    Allowed Roles: ["slo"]
    """

    user = info.context.user
    if user is None or user.get("role") not in ["slo"]:
        raise ValueError("You do not have permission to access this resource.")

    event = eventsdb.find_one(
        {
            "_id": details.eventid,
            "status.state": Event_State_Status.approved.value,  # type: ignore
            "datetimeperiod.1": {
                "$lt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            },
        }
    )
    if event is None:
        raise ValueError("Event not found.")

    # Get current time
    current_time = datetime.now(timezone)
    time_str = current_time.strftime("%d-%m-%Y %I:%M %p")

    upd_ref = eventsdb.update_one(
        {"_id": details.eventid},
        {
            "$set": {
                "bills_status": {
                    "state": details.state,
                    "updated_time": time_str,
                    "slo_comment": details.slo_comment,
                }
            }
        },
    )
    if upd_ref.modified_count == 0:
        raise ValueError("Bills status not updated")

    event = eventsdb.find_one({"_id": details.eventid})

    return Bills_Status(**event["bills_status"])

# register all mutations
mutations = [updateBillsStatus]