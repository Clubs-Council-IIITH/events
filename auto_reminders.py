from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import eventsdb
from mailing import triggerMail
from mailing_templates import (
    EVENT_BILL_REMINDER_BODY,
    EVENT_BILL_REMINDER_SUBJECT,
    EVENT_REPORT_REMINDER_BODY,
    EVENT_REPORT_REMINDER_SUBJECT,
)
from models import Event
from mtypes import Bills_State_Status, Event_State_Status, timezone
from utils import get_bot_cookie, getClubDetails, getEventLink, getRoleEmails


async def check_for_bill_status():
    """
    Checks for events that have pending bills and sends reminder emails.
    This function is meant to be run on a schedule.

    Args:
    None

    Returns:
    None
    """
    # find events ended in past 4 days, that have
    # bill status not submitted and event is complete
    current_time = datetime.now(timezone)
    week_ago = current_time - timedelta(days=7)

    pending_bills = await eventsdb.find(
        {
            "datetimeperiod.1": {
                "$gte": week_ago.isoformat(),
                "$lte": current_time.isoformat(),
            },
            "status.state": Event_State_Status.approved.value,
            "budget": {"$exists": True, "$ne": []},
            "bills_status.state": Bills_State_Status.not_submitted.value,
        }
    ).to_list(length=None)

    if len(pending_bills) == 0:
        # print("No pending bills found")
        return

    bot_cookie = await get_bot_cookie()

    for event in pending_bills:
        event_instance = Event.model_validate(event)

        try:
            clubDetails = await getClubDetails(event_instance.clubid, None)

            if len(clubDetails.keys()) == 0:
                print(f"Club does not exist for event {event_instance.code}")
                continue

            mail_club = clubDetails["email"]
            clubname = clubDetails["name"]

            # Check if budget exists for the event
            if event_instance.budget and len(event_instance.budget) > 0:
                total_budget = sum(
                    item.amount for item in event_instance.budget
                )

            # Prepare email
            mail_subject = EVENT_BILL_REMINDER_SUBJECT.safe_substitute(
                event_id=event_instance.code,
                event=event_instance.name,
            )

            mail_body = EVENT_BILL_REMINDER_BODY.safe_substitute(
                club=clubname,
                event=event_instance.name,
                eventlink=getEventLink(event_instance.code),
                total_budget=total_budget,
            )

            await triggerMail(
                "events_autoemailing",
                mail_subject,
                mail_body,
                toRecipients=[mail_club],
                ccRecipients=await getRoleEmails("cc"),
                cookies=bot_cookie,
            )

        except Exception as e:
            print(
                f"Error sending reminder for event {event_instance.code}: {e}"
            )


async def check_for_ended_events():
    """
    Checks for events that have ended on the last day and sends reminder emails.
    This function is meant to be run on a schedule.

    Args:
    None

    Returns:
    None
    """  # noqa: E501
    current_time = datetime.now(timezone)
    one_day_ago = current_time - timedelta(days=1)

    # find events that ended today
    ended_events = await eventsdb.find(
        {
            "datetimeperiod.1": {
                "$gte": one_day_ago.isoformat(),
                "$lte": current_time.isoformat(),
            },
            "status.state": Event_State_Status.approved.value,
            "event_report_submitted": {"$ne": True},
        }
    ).to_list(length=None)

    if len(ended_events) == 0:
        # print("No ended events found")
        return

    bot_cookie = await get_bot_cookie()

    for event in ended_events:
        event_instance = Event.model_validate(event)

        try:
            clubDetails = await getClubDetails(event_instance.clubid, None)

            if len(clubDetails.keys()) == 0:
                print(f"Club does not exist for event {event_instance.code}")
                continue

            mail_club = clubDetails["email"]
            clubname = clubDetails["name"]

            # Prepare email
            mail_subject = EVENT_REPORT_REMINDER_SUBJECT.safe_substitute(
                event_id=event_instance.code,
                event=event_instance.name,
            )

            mail_body = EVENT_REPORT_REMINDER_BODY.safe_substitute(
                club=clubname,
                event=event_instance.name,
                eventlink=getEventLink(event_instance.code),
            )

            await triggerMail(
                "events_autoemailing",
                mail_subject,
                mail_body,
                toRecipients=[mail_club],
                cookies=bot_cookie,
            )

        except Exception as e:
            print(
                f"Error sending reminder for event {event_instance.code}: {e}"
            )


def init_event_reminder_system():
    """
    Initializes the event reminder system using AsyncIOScheduler.
    """
    scheduler = AsyncIOScheduler(timezone=timezone)
    scheduler.add_job(check_for_ended_events, "cron", hour=0, minute=0)
    scheduler.add_job(
        check_for_bill_status, "cron", day_of_week="sun", hour=12, minute=0
    )
    scheduler.start()
