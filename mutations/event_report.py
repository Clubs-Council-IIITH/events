from datetime import datetime

import strawberry
from fastapi.encoders import jsonable_encoder

from db import event_reportsdb, eventsdb
from models import EventReport
from mtypes import Event_State_Status
from otypes import EventReportType, Info, InputEventReport
from utils import getMember


@strawberry.mutation
def addEventReport(details: InputEventReport, info: Info) -> EventReportType:
    """
    Adds an event report after completion of the event
    
    Args:
        details (InputEventReport): The details of the event report to be added.
        info (Info): The context information of user for the request.
    
    Returns:
        EventReportType: The details of the added event report.

    Raises:
        ValueError: User not authenticated
        ValueError: User not authorized
        ValueError: Event ID is required
        ValueError: Event not found
        ValueError: User not authorized
        ValueError: Event report already exists
        ValueError: Submitted by is not a valid member
    """

    user = info.context.user
    if not user:
        raise ValueError("User not authenticated")

    user_role = user["role"]
    if user_role not in ["club"]:
        raise ValueError("User not authorized")

    eventid = details.eventid
    if not eventid:
        raise ValueError("Event ID is required")
    event = eventsdb.find_one(
        {
            "_id": eventid,
            "datetimeperiod.1": {
                "$lt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            },
            "status.state": Event_State_Status.approved.value,
        }
    )
    if not event:
        raise ValueError("Event not found")
    if user_role == "club" and event["clubid"] != user["uid"]:
        raise ValueError("User not authorized")

    searchspace = {
        "event_id": eventid,
    }

    event_report = event_reportsdb.find_one(searchspace)

    if event_report:
        raise ValueError("Event report already exists")
    
    # Check if submitted_by is valid
    cid = event["clubid"]
    uid = details.submitted_by
    if not getMember(cid, uid, info.context.cookies):
        raise ValueError("Submitted by is not a valid member")

    report_dict = jsonable_encoder(details.to_pydantic())
    report_dict["event_id"] = details.eventid
    event_report_id = event_reportsdb.insert_one(report_dict).inserted_id
    event_report = event_reportsdb.find_one({"_id": event_report_id})

    # Update event report submitted status to True
    eventsdb.update_one(
        {"_id": eventid},
        {"$set": {"event_report_submitted": True}},
    )

    return EventReportType.from_pydantic(
        EventReport.model_validate(event_report)
    )


mutations = [addEventReport]
