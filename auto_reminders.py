import asyncio
import threading
import time
from datetime import datetime, timedelta

from schedule import Scheduler

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


def run_async_job(coro):
    asyncio.run(coro())


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

    pending_bills = eventsdb.find(
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

            triggerMail(
                "events_autoemailing",
                mail_subject,
                mail_body,
                toRecipients=[mail_club],
                ccRecipients=await getRoleEmails("cc"),
                cookies=bot_cookie,
            )
            time.sleep(5)

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
    ended_events = list(
        eventsdb.find(
            {
                "datetimeperiod.1": {
                    "$gte": one_day_ago.isoformat(),
                    "$lte": current_time.isoformat(),
                },
                "status.state": Event_State_Status.approved.value,
                "event_report_submitted": {"$ne": True},
            }
        )
    )

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

            triggerMail(
                "events_autoemailing",
                mail_subject,
                mail_body,
                toRecipients=[mail_club],
                cookies=bot_cookie,
            )
            time.sleep(5)

        except Exception as e:
            print(
                f"Error sending reminder for event {event_instance.code}: {e}"
            )


async def start_scheduler_instance(scheduler_instance: Scheduler):
    """
    Continuously runs the scheduler instance to execute any pending scheduled tasks.

    This function runs an infinite loop that checks for pending tasks in the provided
    scheduler instance and executes them. It pauses for one second between each check
    to prevent excessive CPU usage.

    Args:
        scheduler_instance (Scheduler): The scheduler object responsible for managing and running scheduled tasks.

    Returns:
    None
    """  # noqa: E501

    while True:
        scheduler_instance.run_pending()
        await asyncio.sleep(1)


# start the scheduler in a background thread
def init_event_reminder_system():
    """
    Initializes the event reminder system by starting the scheduler in a background thread.

    Schedulers:
        * Sends reminders for events that have ended in the last day. _Runs every day at 00:00._
        * Sends reminders for events that have pending bills in the last week. _Runs every Sunday at 12:00._

    Args:
    None

    Returns:
    None
    """  # noqa: E501
    ended_scheduler = Scheduler()
    ended_scheduler.every().day.at("00:00", timezone).do(
        run_async_job, check_for_ended_events
    )
    threading.Thread(
        target=start_scheduler_instance, args=(ended_scheduler,), daemon=True
    ).start()

    bill_scheduler = Scheduler()
    bill_scheduler.every().sunday.at("12:00", timezone).do(
        run_async_job, check_for_bill_status
    )
    threading.Thread(
        target=start_scheduler_instance, args=(bill_scheduler,), daemon=True
    ).start()
