"""
Mutation Resolvers for the finances of an event

Contains method that are related to the finances of an event.
Used mostly by the SLO.
"""

from datetime import datetime

import strawberry

from db import eventsdb
from mailing import triggerMail
from mailing_templates import (
    EVENT_BILL_STATUS_BODY_FOR_CLUB,
    EVENT_BILL_STATUS_SUBJECT,
)
from mtypes import (
    Bills_Full_State_Status,
    Bills_Status,
    Event_State_Status,
    timezone,
)
from otypes import Info, InputBillsStatus
from utils import getClubDetails, getEventLink, getRoleEmails


@strawberry.mutation
def updateBillsStatus(details: InputBillsStatus, info: Info) -> Bills_Status:
    """
    Update the bills status of an event
    
    This method is used to update the bills status of an event.
    It is only accessible to the SLO.
    It triggers an email to the organizing club along with Clubs Council in cc recipients regarding the updation in the bills status.

    Inputs:
        details (InputBillsStatus): The details of the bills status to be updated.
        info (Info): The info object containing the user information.

    Returns:
        Bills_Status: The updated bills status of the event.

    Accessible to:
        SLO only.

    Raises Exception:
        You do not have permission to access this resource : If user is not autherized.
        Event not found : If the event whose event id is given is not found.
        Club Email not found : If the club's email is not found.
        Bills status not updated : If the bills status is not updated with respect to the previous state.
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
            "budget": {
                "$exists": True,
                "$ne": [],
            },  # Ensure the budget array exists and is not empty
        }
    )
    if event is None:
        raise ValueError("Event not found.")

    mail_to = getClubDetails(event["clubid"], info.context.cookies).get(
        "email", None
    )
    if not mail_to:
        raise ValueError("Club email not found")

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
    if not event:
        raise ValueError("Event not found")

    cc_to = getRoleEmails("cc")

    mail_uid = user["uid"]
    mail_subject = EVENT_BILL_STATUS_SUBJECT.safe_substitute(
        event=event["name"],
    )
    mail_body = EVENT_BILL_STATUS_BODY_FOR_CLUB.safe_substitute(
        event=event["name"],
        bill_status=getattr(Bills_Full_State_Status, details.state),
        comment=details.slo_comment,
        eventlink=getEventLink(event["code"]),
    )
    # email to club regarding the updation in the bills status
    triggerMail(
        mail_uid,
        mail_subject,
        mail_body,
        toRecipients=[
            mail_to,
        ],
        ccRecipients=cc_to,
        cookies=info.context.cookies,
    )

    return Bills_Status(**event["bills_status"])


# register all mutations
mutations = [updateBillsStatus]
