import strawberry

from db import eventsdb
from mailing import triggerMail
from mailing_templates import (
    REMIND_SLO_APPROVAL_BODY,
    REMIND_SLO_APPROVAL_SUBJECT,
)
from models import Event
from otypes import Info
from utils import getEventLink, getRoleEmails


@strawberry.mutation
async def remindSLO(info: Info, eventid: str) -> bool:
    """
    Sends a reminder email to the SLO to approve the event.

    Args:
        eventid (str): The ID of the event.
        info (Info): The context of the request for user info.

    Returns:
        (bool): Success or Failiure

    Raises:
        Exception: If the user is not authorized or the event does not exist.
    """
    user = info.context.user

    if user is None or user.get("role") != "cc":
        raise Exception("You do not have permission to access this resource.")

    event_ref = await eventsdb.find_one({"_id": eventid})
    if not event_ref:
        raise Exception("Event not found.")

    event_instance = Event.model_validate(event_ref)
    slo_emails = await getRoleEmails("slo")

    if not slo_emails:
        raise Exception("No SLO emails found to send a reminder.")

    # format email using the new concise template
    mail_uid = user["uid"]
    mail_subject = REMIND_SLO_APPROVAL_SUBJECT.safe_substitute(
        event=event_instance.name
    )
    mail_body = REMIND_SLO_APPROVAL_BODY.safe_substitute(
        event_id=event_instance.code,
        club=event_instance.clubid,
        event=event_instance.name,
        start_time=event_instance.datetimeperiod[0].strftime("%d-%m-%Y %H:%M"),
        end_time=event_instance.datetimeperiod[1].strftime("%d-%m-%Y %H:%M"),
        location=", ".join(event_instance.location)
        if event_instance.location
        else "N/A",
        eventlink=getEventLink(event_instance.code),
    )

    # send email
    await triggerMail(
        mail_uid,
        mail_subject,
        mail_body,
        toRecipients=slo_emails,
        cookies=info.context.cookies,
    )

    return True


mutations = [remindSLO]
