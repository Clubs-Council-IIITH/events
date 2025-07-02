from datetime import datetime, timedelta

import strawberry
from fastapi.encoders import jsonable_encoder

from db import event_reportsdb, eventsdb
from models import EventReport
from mtypes import Event_State_Status, timezone
from otypes import EventReportType, Info, InputEventReport
from utils import getMember


@strawberry.mutation
async def addEventReport(details: InputEventReport, info: Info) -> EventReportType:
    """
    Adds an event report after completion of the event

    Args:
        details (InputEventReport): The details of the event report to be added.
        info (Info): The context information of user for the request.

    Returns:
        (EventReportType): The details of the added event report.

    Raises:
        ValueError: User not authenticated
        ValueError: User not authorized
        ValueError: Event ID is required
        ValueError: Event not found
        ValueError: User not authorized
        ValueError: Event report already exists
        ValueError: Submitted by is not a valid member
    """  # noqa: E501

    user = info.context.user
    if not user:
        raise ValueError("User not authenticated")

    user_role = user["role"]
    if user_role not in ["club"]:
        raise ValueError("User not authorized")

    eventid = details.eventid
    if not eventid:
        raise ValueError("Event ID is required")
    event = await eventsdb.find_one(
        {
            "_id": eventid,
            "datetimeperiod.1": {
                "$lt": datetime.now(timezone).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
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

    event_report = await event_reportsdb.find_one(searchspace)

    if event_report:
        raise ValueError("Event report already exists")

    # Check if submitted_by is valid
    cid = event["clubid"]
    uid = details.submitted_by
    if not await getMember(cid, uid, info.context.cookies):
        raise ValueError("Submitted by is not a valid member")

    report_dict = jsonable_encoder(details.to_pydantic())
    report_dict["event_id"] = details.eventid
    event_report_id = await event_reportsdb.insert_one(report_dict).inserted_id
    event_report = await event_reportsdb.find_one({"_id": event_report_id})

    # Update event report submitted status to True
    await eventsdb.update_one(
        {"_id": eventid},
        {"$set": {"event_report_submitted": True}},
    )

    return EventReportType.from_pydantic(
        EventReport.model_validate(event_report)
    )


@strawberry.mutation
async def editEventReport(details: InputEventReport, info: Info) -> EventReportType:
    """
    Edits an event report after completion of the event

    Args:
        details (InputEventReport): The details of the event report to be edited.
        info (Info): The context information of user for the request.

    Returns:
        (EventReportType): The details of the edited event report.

    Raises:
        ValueError: User not authenticated
        ValueError: User not authorized
        ValueError: Event ID is required
        ValueError: Event not found
        ValueError: User not authorized
        ValueError: Event report not found
        ValueError: Submitted by is not a valid member
    """  # noqa: E501

    user = info.context.user
    if not user:
        raise ValueError("User not authenticated")

    user_role = user["role"]
    if user_role not in ["club", "cc", "slo"]:
        raise ValueError("User not authorized")

    eventid = details.eventid
    if not eventid:
        raise ValueError("Event ID is required")

    event = await eventsdb.find_one(
        {
            "_id": eventid,
            "datetimeperiod.1": {
                "$lt": datetime.now(timezone).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
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

    event_report = await event_reportsdb.find_one(searchspace)

    if not event_report:
        raise ValueError("Event report not found")

    submitted_time = datetime.strptime(
        event_report["submitted_time"], "%Y-%m-%dT%H:%M:%S.%fZ"
    )

    if user_role in ["club", "cc"]:
        edit_window = timedelta(days=2)
    elif user_role == "slo":
        edit_window = timedelta(days=14)

    if submitted_time + edit_window < datetime.now():
        raise ValueError("Event report can't be updated")

    report_dict = jsonable_encoder(details.to_pydantic())
    report_dict["event_id"] = details.eventid
    await event_reportsdb.update_one(searchspace, {"$set": report_dict})
    event_report = await event_reportsdb.find_one(searchspace)

    return EventReportType.from_pydantic(
        EventReport.model_validate(event_report)
    )


mutations = [addEventReport, editEventReport]
