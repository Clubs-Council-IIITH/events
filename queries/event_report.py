import strawberry

from db import event_reportsdb, eventsdb
from models import EventReport
from otypes import EventReportType, Info


@strawberry.field
def eventReport(eventid: str, info: Info) -> EventReportType:
    """
    Get the event report of an event
    returns the event report
    """

    user = info.context.user
    if not user:
        raise ValueError("User not authenticated")

    user_role = user["role"]
    if user_role not in ["cc", "slo", "club"]:
        raise ValueError("User not authorized")

    event = eventsdb.find_one({"_id": eventid, "event_report_submitted": True})
    if not event:
        raise ValueError("Event not found")
    if user_role == "club" and event["clubid"] != user["uid"]:
        raise ValueError("User not authorized")

    event_report = event_reportsdb.find_one(
        {
            "event_id": eventid,
        }
    )

    if not event_report:
        raise ValueError("Event report not found")

    return EventReportType.from_pydantic(
        EventReport.model_validate(event_report)
    )


queries = [eventReport]
