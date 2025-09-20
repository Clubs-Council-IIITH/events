from datetime import datetime

import strawberry

from db import eventsdb
from mailing import triggerMail
from mailing_templates import (
    BILL_SUBMISSION_BODY_FOR_SLO,
    BILL_SUBMISSION_SUBJECT,
    EVENT_BILL_STATUS_BODY_FOR_CLUB,
    EVENT_BILL_STATUS_SUBJECT,
)
from models import Event
from mtypes import (
    Bills_Full_State_Status,
    Bills_State_Status,
    Bills_Status,
    Event_State_Status,
    timezone,
)
from otypes import Info, InputBillsStatus, InputBillsUpload
from utils import (
    delete_file,
    getClubDetails,
    getEventFinancesLink,
    getEventLink,
    getRoleEmails,
)


@strawberry.mutation
async def updateBillsStatus(
    details: InputBillsStatus, info: Info
) -> Bills_Status:
    """
    Updates the bills status of an event for SLO along with
    triggering an email to the organizing club.

    Args:
        details (otypes.InputBillsStatus): The details of the bills status to be updated.
        info (otypes.Info): The info object containing the user information.

    Returns:
        (mtypes.Bills_Status): The updated bills status of the event.

    Raises:
        ValueError: You do not have permission to access this resource.
        ValueError: Event not found.
        ValueError: Club email not found.
        ValueError: Event bill status not updated.
    """  # noqa: E501

    user = info.context.user
    if user is None or user.get("role") not in ["slo"]:
        raise ValueError("You do not have permission to access this resource.")

    # Get current time
    current_time = datetime.now(timezone)
    time_str = current_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    event = await eventsdb.find_one(
        {
            "_id": details.eventid,
            "status.state": Event_State_Status.approved.value,  # type: ignore
            "datetimeperiod.1": {"$lt": time_str},
            "budget": {
                "$exists": True,
                "$ne": [],
            },
        }
    )
    if event is None:
        raise ValueError("Event not found.")

    mail_to = (
        await getClubDetails(event["clubid"], info.context.cookies)
    ).get("email", None)
    if not mail_to:
        raise ValueError("Club email not found")

    upd_ref = await eventsdb.update_one(
        {"_id": details.eventid},
        {
            "$set": {
                "bills_status.state": details.state,
                "bills_status.updated_time": time_str,
                "bills_status.slo_comment": details.slo_comment,
            }
        },
    )
    if upd_ref.modified_count == 0:
        raise ValueError("Bills status not updated")

    event = await eventsdb.find_one({"_id": details.eventid})
    if not event:
        raise ValueError("Event not found")

    cc_to = await getRoleEmails("cc")

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
    await triggerMail(
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


@strawberry.mutation
async def addBill(details: InputBillsUpload, info: Info) -> bool:
    """
    Submits a bill for an approved event and notifies the Student Life OfFix the docsstrings to specify the custom types correctly, like mtypes.Event_Location in place of Event_Location (modulename.type)fice (SLO).

    Args:
        details (otypes.InputBillsUpload): Contains event ID and filename of the uploaded bill.
        info (otypes.Info): Context object containing user information and cookies.

    Returns:
        bool: True if the bill was successfully added and notifications sent.

    Raises:
        ValueError: If the user lacks permission, the event isn't found, or the update fails.
        Exception: If no SLO email addresses are found in the system.
    """  # noqa: E501

    user = info.context.user
    if user is None or user.get("role") not in ["club"]:
        raise ValueError("You do not have permission to access this resource.")

    current_time = datetime.now(timezone)
    time_str = current_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    event = await eventsdb.find_one(
        {
            "_id": details.eventid,
            "status.state": Event_State_Status.approved.value,  # type: ignore
            "datetimeperiod.1": {"$lt": time_str},
            "budget": {
                "$exists": True,
                "$ne": [],
            },
        }
    )

    if event is None:
        raise ValueError("Event not found.")

    if event["clubid"] != user.get("uid"):
        raise ValueError("You do not have permission to access this resource.")

    # reverse compatibility
    bill = event.get("bills_status")
    if not bill:
        raise ValueError("This event doesn't support bill upload feature")

    curr_state = bill.get("state")
    if not curr_state or curr_state not in [
        Bills_State_Status.not_submitted.value,
        Bills_State_Status.rejected.value,
    ]:
        raise ValueError(
            "Event already has bill, you are not allowed to submit"
        )

    new_budget = [
        {
            "amount": item.amount,
            "description": item.description,
            "advance": item.advance,
            "billno": item.billno,  # Include the billno field
            "amount_used": item.amount_used or 0,
        }
        for item in details.budget
    ]

    # Validate the new budget total
    if sum(item["amount"] for item in new_budget) != sum(
        item["amount"] for item in event["budget"]
    ):
        raise ValueError("New budget total doesn't match the old budget total")

    # change state to submitted and put filename
    upd_ref = await eventsdb.update_one(
        {"_id": details.eventid},
        {
            "$set": {
                "bills_status": {
                    "state": Bills_State_Status.submitted,
                    "submitted_time": time_str,
                    "updated_time": time_str,
                    "filename": details.filename,
                },
                "budget": new_budget,
            }
        },
    )
    if upd_ref.modified_count == 0:
        raise ValueError("Bills status not updated")

    # if already a bills_status file exists, then delete it
    if bill.get("filename"):
        try:
            await delete_file(bill["filename"])
        except Exception as e:
            print(f"Error deleting file: {e}")

    event = await eventsdb.find_one({"_id": details.eventid})
    if not event:
        raise ValueError("Event not found")

    event_instance = Event.model_validate(event)
    total_budget = sum(item.amount for item in event_instance.budget)
    total_budget_used = sum(
        item.amount_used for item in event_instance.budget if item.amount_used
    )

    clubname = (
        await getClubDetails(event["clubid"], info.context.cookies)
    ).get("name", None)
    cc_to = await getRoleEmails("cc")
    slo_emails = await getRoleEmails("slo")

    if not slo_emails:
        raise Exception("No SLO emails found to send a reminder.")

    mail_uid = user["uid"]
    mail_subject = BILL_SUBMISSION_SUBJECT.safe_substitute(
        event_id=event_instance.code,
        event=event_instance.name,
    )

    mail_body = BILL_SUBMISSION_BODY_FOR_SLO.safe_substitute(
        club=clubname,
        event_id=event_instance.code,
        event=event["name"],
        event_date=event_instance.datetimeperiod[0].strftime("%d-%m-%Y %H:%M"),
        total_budget=total_budget,
        total_budget_used=total_budget_used,
        eventfinancelink=getEventFinancesLink(event_instance.id),
    )

    await triggerMail(
        mail_uid,
        mail_subject,
        mail_body,
        toRecipients=[
            slo_emails,
        ],
        ccRecipients=cc_to,
        cookies=info.context.cookies,
    )

    return True


# register all mutations
mutations = [updateBillsStatus, addBill]
