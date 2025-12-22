from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import strawberry

from db import event_reportsdb, eventsdb
from models import EventReport
from otypes import EventReportType, Info


@strawberry.field
async def eventReport(eventid: str, info: Info) -> EventReportType:
    """
    This field retrieves the event report of an event for CC, SLO, and Club
    users.
    Only authenticated users with appropriate roles can access the report.

    Args:
        eventid (str): The id of the event
        info (otypes.Info): The user details

    Returns:
        (otypes.EventReportType): The event report of the event

    Raises:
        ValueError: User not authenticated
        ValueError: User not authorized
        ValueError: Event not found
        ValueError: Event report not found
    """

    user = info.context.user
    if not user:
        raise ValueError("User not authenticated")

    user_role = user["role"]
    if user_role not in ["cc", "slo", "club"]:
        raise ValueError("User not authorized")

    event = await eventsdb.find_one(
        {"_id": eventid, "event_report_submitted": True}
    )
    if not event:
        raise ValueError("Event not found")
    if (
        user_role == "club"
        and event["clubid"] != user["uid"]
        and (
            event["collabclubs"] is None
            or user["uid"] not in event["collabclubs"]
        )
    ):
        raise ValueError("User not authorized")

    event_report = await event_reportsdb.find_one(
        {
            "event_id": eventid,
        }
    )

    if not event_report:
        raise ValueError("Event report not found")

    return EventReportType.from_pydantic(
        EventReport.model_validate(event_report)
    )


@strawberry.field
async def isEventReportsSubmitted(clubid: str, info: Info) -> bool:
    """
    This field checks if all event reports have been submitted for a club.

    Args:
        clubid (str): The id of the club
        info (otypes.Info): The user details

    Returns:
        (bool): True if all event reports have been submitted, False otherwise

    Raises:
        ValueError: User not authenticated
        ValueError: User not authorized
    """
    user = info.context.user
    if not user:
        raise ValueError("User not authenticated")

    user_role = user["role"]
    if user_role not in ["cc", "slo", "club"]:
        raise ValueError("User not authorized")

    report_check_lt = (
        datetime.now(ZoneInfo("UTC")) - timedelta(days=7)
    ).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    report_check_gt = datetime(2025, 11, 15, tzinfo=ZoneInfo("UTC")).strftime(
        "%Y-%m-%dT%H:%M:%S+00:00"
    )

    events = await eventsdb.find(
        {
            "clubid": clubid,
            "status.state": {"$in": ["approved"]},
            "datetimeperiod.1": {
                "$lt": report_check_lt,
                "$gt": report_check_gt,
            },
            "event_report_submitted": {"$ne": True},
        }
    ).to_list(length=None)

    return not len(events) > 0


queries = [eventReport, isEventReportsSubmitted]
