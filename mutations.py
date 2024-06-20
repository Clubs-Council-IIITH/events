import os
from datetime import datetime, timedelta

import strawberry
from fastapi.encoders import jsonable_encoder
from pydantic import HttpUrl, parse_obj_as

from db import eventsdb
from mailing import triggerMail
from mailing_templates import (
    APPROVED_EVENT_BODY_FOR_CLUB,
    CLUB_EVENT_SUBJECT,
    DELETE_EVENT_BODY_FOR_CC,
    DELETE_EVENT_BODY_FOR_CLUB,
    PROGRESS_EVENT_BODY,
    PROGRESS_EVENT_BODY_FOR_SLO,
    PROGRESS_EVENT_SUBJECT,
    SUBMIT_EVENT_BODY_FOR_CLUB,
)

# import all models and types
from models import Event
from mtypes import (
    Audience,
    BudgetType,
    Event_Full_Location,
    Event_Location,
    Event_Mode,
    Event_State_Status,
    timezone,
)
from otypes import EventType, Info, InputEditEventDetails, InputEventDetails
from utils import (
    getClubNameEmail,
    getEventCode,
    getEventLink,
    getMember,
    getRoleEmails,
    getUser,
)

inter_communication_secret_global = os.getenv("INTER_COMMUNICATION_SECRET")


@strawberry.mutation
def createEvent(details: InputEventDetails, info: Info) -> EventType:
    """
    create event with given details if user has permission
    return the event
    """
    user = info.context.user

    if (
        not user
        or not details.clubid
        or not (
            (user["role"] == "club" and user["uid"] == details.clubid)
            or (user["role"] == "cc")  # allow CC to create events too
        )
    ):
        raise Exception("You do not have permission to access this resource.")

    # Check if the start time is before the end time
    if details.datetimeperiod[0] >= details.datetimeperiod[1]:
        raise Exception("Start time cannot be after end time.")

    event_instance = Event(
        name=details.name,
        clubid=details.clubid,
        datetimeperiod=tuple(details.datetimeperiod),
        poc=details.poc,
    )
    if details.mode is not None:
        event_instance.mode = Event_Mode(details.mode)
    if details.location is not None:
        event_instance.location = [
            Event_Location(loc) for loc in details.location
        ]
    if details.description is not None:
        event_instance.description = details.description
    if details.poster is not None:
        event_instance.poster = details.poster
    if details.audience is not None:
        event_instance.audience = [Audience(aud) for aud in details.audience]
    if details.link is not None:
        event_instance.link = parse_obj_as(HttpUrl, details.link)
    if details.equipment is not None:
        event_instance.equipment = details.equipment
    if details.additional is not None:
        event_instance.additional = details.additional
    if details.population is not None:
        event_instance.population = details.population
    if details.budget is not None:
        event_instance.budget = list(
            map(
                lambda x: BudgetType(
                    amount=x.amount,
                    description=x.description,
                    advance=x.advance,
                ),
                details.budget,
            )
        )

    # Check POC Details Exist or not
    if not getMember(
        details.clubid, details.poc, cookies=info.context.cookies
    ):
        raise Exception("Member Details for POC does not exist")

    # if creator is CC, set state to approved
    if user["role"] == "cc":
        event_instance.status.state = Event_State_Status.pending_cc
        # event_instance.status.state = Event_State_Status.approved
        # event_instance.status.budget = True
        # event_instance.status.room = True
    else:
        event_instance.status.state = Event_State_Status.incomplete

    # set event code
    event_instance.code = getEventCode(
        details.clubid, details.datetimeperiod[0]
    )

    created_id = eventsdb.insert_one(
        jsonable_encoder(event_instance)
    ).inserted_id
    created_event = Event.parse_obj(eventsdb.find_one({"_id": created_id}))

    return EventType.from_pydantic(created_event)


@strawberry.mutation
def editEvent(details: InputEditEventDetails, info: Info) -> EventType:
    """
    edit event with given details if user has permission
    return the event
    """
    user = info.context.user
    allowed_roles = ["cc", "slo"]

    if user is None:
        raise Exception("Not Authenticated!")

    if (details.clubid != user["uid"] or user["role"] != "club") and user[
        "role"
    ] not in allowed_roles:
        raise Exception("Not Authenticated to access this API")

    if details.datetimeperiod is not None:
        if details.datetimeperiod[0] >= details.datetimeperiod[1]:
            raise Exception(
                "Start datetime cannot be same/after end datetime."
            )

    event_ref = eventsdb.find_one({"_id": details.eventid})

    if not event_ref:
        raise Exception("Event does not exist.")

    # if the update is done by CC, set state to approved
    # else set status to incomplete
    updates = {
        "status.state": event_ref["status"]["state"],
        # if user["role"] == "cc"
        # else Event_State_Status.incomplete,
        "status.budget": event_ref["status"]["budget"],
        # if user["role"] == "cc"
        # else False,
        "status.room": event_ref["status"]["room"],
        # if user["role"] == "cc"
        # else False,
    }

    updatable = user["role"] in allowed_roles or (
        user["role"] == "club"
        and event_ref["status"]["state"] == Event_State_Status.incomplete
    )

    if details.name is not None and updatable:
        updates["name"] = details.name
    if details.datetimeperiod is not None and updatable:
        updates["datetimeperiod"] = details.datetimeperiod
    if details.mode is not None and updatable:
        updates["mode"] = Event_Mode(details.mode)
    if details.location is not None and updatable:
        # updates["status.room"] = False or user["role"] == "cc"
        updates["location"] = [Event_Location(loc) for loc in details.location]
    if details.poc is not None and event_ref.get("poc", None) != details.poc:
        updates["poc"] = details.poc
        # Check POC Details Exist or not
        if not getMember(
            details.clubid, details.poc, cookies=info.context.cookies
        ):
            raise Exception("Member Details for POC does not exist")
    if details.description is not None:
        updates["description"] = details.description
    if details.poster is not None:
        updates["poster"] = details.poster
    if details.audience is not None:
        updates["audience"] = [Audience(aud) for aud in details.audience]
    if details.link is not None:
        updates["link"] = details.link
    if details.equipment is not None:
        updates["equipment"] = details.equipment
    if details.additional is not None:
        updates["additional"] = details.additional
    if details.population is not None:
        updates["population"] = details.population
    if details.budget is not None and updatable:
        # updates["status.budget"] = False or user["role"] == "cc"
        updates["budget"] = list(
            map(
                lambda x: BudgetType(
                    amount=x.amount,
                    description=x.description,
                    advance=x.advance,
                ),
                details.budget,
            )
        )

    query = {
        "_id": details.eventid,
        "clubid": user["uid"]
        if (user is not None and user["role"] == "club")
        else details.clubid
        if (user["role"] in allowed_roles)
        else None,
    }

    updation = {"$set": jsonable_encoder(updates)}

    upd_ref = eventsdb.update_one(query, updation)
    if upd_ref.matched_count == 0:
        raise Exception("You do not have permission to access this resource.")

    event_ref = eventsdb.find_one({"_id": details.eventid})
    return EventType.from_pydantic(Event.parse_obj(event_ref))


@strawberry.mutation
def progressEvent(
    eventid: str,
    info: Info,
    cc_progress_budget: bool | None = None,
    cc_progress_room: bool | None = None,
    cc_approver: str | None = None,
) -> EventType:
    """
    progress the event state status for different users
    returns the new event details

    initially, the event is `incomplete`
    after the club fills all the details, they progress it
    cc chooses to progress the state status, the budget status and the room status
    if budget status is unapproved, the event is `pending_budget`, else skip to next
    after budget is approved (through any track),
    if room status is unapproved, the event is `pending_room`, else skip to next
    after room is approved (through any track), the event is `approved`
    once the event is over, the club or cc can change the state to `completed`
    """  # noqa: E501
    noaccess_error = Exception(
        "Can not access event. Either it does not exist or user does not have perms."  # noqa: E501
    )

    user = info.context.user

    event_ref = eventsdb.find_one({"_id": eventid})
    if event_ref is None or user is None:
        raise noaccess_error
    event_instance = Event.parse_obj(event_ref)

    # get current time
    current_time = datetime.now(timezone)
    time_str = current_time.strftime("%d-%m-%Y %I:%M %p")

    if event_instance.status.state == Event_State_Status.incomplete:
        if user["role"] != "club" or user["uid"] != event_instance.clubid:
            raise noaccess_error
        updation = {
            "budget": False,
            # or sum([b.amount for b in event_instance.budget]) == 0,
            "room": False,
            #   or len(event_instance.location) == 0,
            "state": Event_State_Status.pending_cc.value,
            "cc_approver": None,
            "slc_approver": None,
            "slo_approver": None,
            "submission_time": time_str,
            "cc_approver_time": "Not Approved",
            "slc_approver_time": "Not Approved",
            "slo_approver_time": "Not Approved",
        }

    elif event_instance.status.state == Event_State_Status.pending_cc:
        if user["role"] != "cc":
            raise noaccess_error
        updation = {
            "budget": event_instance.status.budget,
            # or sum([b.amount for b in event_instance.budget]) == 0,
            "room": event_instance.status.room,
            #   or len(event_instance.location) == 0,
            "cc_approver": user["uid"],
            "slc_approver": event_instance.status.slc_approver,
            "slo_approver": event_instance.status.slo_approver,
            "cc_approver_time": time_str,
            "slc_approver_time": event_instance.status.slc_approver_time,
            "slo_approver_time": event_instance.status.slo_approver_time,
            "submission_time": event_instance.status.submission_time,
        }
        if cc_progress_budget is not None:
            updation["budget"] = cc_progress_budget
        if cc_progress_room is not None:
            updation["room"] = cc_progress_room
        if cc_approver is not None:
            updation["cc_approver"] = cc_approver
        else:
            raise Exception("CC Approver is required to progress the event.")

        if not updation["budget"]:
            updation["state"] = Event_State_Status.pending_budget.value
        elif not updation["room"]:
            # if budget is approved
            updation["slc_approver_time"] = None
            updation["state"] = Event_State_Status.pending_room.value
        else:
            # if both are approved
            updation["slc_approver_time"] = None
            updation["slo_approver_time"] = None
            updation["state"] = Event_State_Status.approved.value

    elif event_instance.status.state == Event_State_Status.pending_budget:
        if user["role"] != "slc":
            raise noaccess_error
        assert event_instance.status.budget is False
        updation = {
            "budget": True,
            "room": event_instance.status.room,
            #   | len(event_instance.location) == 0,
            "slc_approver": user["uid"],
            "slo_approver": event_instance.status.slo_approver,
            "cc_approver": event_instance.status.cc_approver,
            "cc_approver_time": event_instance.status.cc_approver_time,
            "slc_approver_time": time_str,
            "slo_approver_time": event_instance.status.slo_approver_time,
            "submission_time": event_instance.status.submission_time,
        }

        if not updation["room"]:
            updation["state"] = Event_State_Status.pending_room.value
        else:
            updation["slo_approver_time"] = time_str
            updation["state"] = Event_State_Status.approved.value

    elif event_instance.status.state == Event_State_Status.pending_room:
        if user["role"] != "slo":
            raise noaccess_error
        assert event_instance.status.budget is True
        assert event_instance.status.room is False
        updation = {
            "budget": event_instance.status.budget,
            "room": True,
            "state": Event_State_Status.approved.value,
            "slo_approver": user["uid"],
            "slc_approver": event_instance.status.slc_approver,
            "cc_approver": event_instance.status.cc_approver,
            "cc_approver_time": event_instance.status.cc_approver_time,
            "slc_approver_time": event_instance.status.slc_approver_time,
            "slo_approver_time": time_str,
            "submission_time": event_instance.status.submission_time,
        }

    elif event_instance.status.state == Event_State_Status.approved:
        if user["role"] != "cc" and (
            user["role"] != "club" or user["uid"] != event_instance.clubid
        ):
            raise noaccess_error

        updation = {
            "budget": event_instance.status.budget,
            "room": event_instance.status.room,
            "state": Event_State_Status.approved.value,
            "submission_time": event_instance.status.submission_time,
            "cc_approver": event_instance.status.cc_approver,
            "slc_approver": event_instance.status.slc_approver,
            "slo_approver": event_instance.status.slo_approver,
            "cc_approver_time": event_instance.status.cc_approver_time,
            "slc_approver_time": event_instance.status.slc_approver_time,
            "slo_approver_time": event_instance.status.slo_approver_time,
        }

    upd_ref = eventsdb.update_one(
        {"_id": eventid}, {"$set": {"status": updation}}
    )
    if upd_ref.matched_count == 0:
        raise noaccess_error

    event_ref = eventsdb.find_one({"_id": eventid})
    updated_event_instance = Event.parse_obj(event_ref)

    # trigger mail notification

    # Data Preparation for the mailing
    mail_uid = user["uid"]
    mail_club = getClubNameEmail(
        updated_event_instance.clubid, email=True, name=True
    )

    if mail_club is None:
        raise Exception("Club does not exist.")
    else:
        clubname, mail_club = mail_club

    mail_event_title = updated_event_instance.name
    mail_eventlink = getEventLink(updated_event_instance.code)
    mail_description = updated_event_instance.description
    if mail_description == "":
        mail_description = "N/A"

    student_count = updated_event_instance.population
    mail_location = ""
    if updated_event_instance.mode == Event_Mode.online:
        mail_location = "online"
        student_count = "N/A"
    else:
        mail_location = ", ".join(
            [
                getattr(Event_Full_Location, loc)
                for loc in updated_event_instance.location
            ]
        )

    equipment, additional, budget = "N/A", "N/A", "N/A"
    if updated_event_instance.equipment:
        equipment = updated_event_instance.equipment
    if updated_event_instance.additional:
        additional = updated_event_instance.additional
    if updated_event_instance.budget:
        budget = "\n"
        budget += "        -----------------------|----------|---------- \n"
        budget += "       | Description           | Amount   | Advance  |\n"
        budget += "       |-----------------------|----------|----------|\n"
        for bdgt in updated_event_instance.budget:
            budget += f"       | {bdgt.description:<21} | {bdgt.amount:<8} | {'Yes' if bdgt.advance else 'No':<8} |\n"
        total_budget = sum(bdgt.amount for bdgt in updated_event_instance.budget)
        budget += "       |-----------------------|----------|----------|\n"
        budget += f"       | Total budget          | {total_budget:<8} |          |\n"
        budget += "        -----------------------|----------|---------- \n"
        
    ist_offset = timedelta(hours=5, minutes=30)
    start_dt = updated_event_instance.datetimeperiod[0] + ist_offset
    end_dt = updated_event_instance.datetimeperiod[1] + ist_offset
    event_start_time = (
        str(start_dt.strftime("%d-%m-%Y"))
        + " "
        + str(start_dt.strftime("%H:%M"))
    )
    event_end_time = (
        str(end_dt.strftime("%d-%m-%Y")) + " " + str(end_dt.strftime("%H:%M"))
    )

    poc = getUser(updated_event_instance.poc, info.context.cookies)
    if not poc:
        raise Exception("POC does not exist.")
    poc_details, poc_phone = poc
    poc_name = poc_details["firstName"] + " " + poc_details["lastName"]
    poc_email = poc_details["email"]
    poc_roll = poc_details["rollno"]
    poc_phone = poc_phone["phone"]
    if not poc_phone:
        poc_phone = "Unknown"
    if not poc_roll:
        poc_roll = "Unknown"

    # Default Mail Subject and Body
    mail_subject = PROGRESS_EVENT_SUBJECT.safe_substitute(
        event=mail_event_title,
    )
    mail_body = PROGRESS_EVENT_BODY.safe_substitute(
        club=clubname,
        event=mail_event_title,
        eventlink=mail_eventlink,
    )

    mail_to = []
    cc_to = []
    if updated_event_instance.status.state == Event_State_Status.pending_cc:
        mail_to = getRoleEmails("cc")

        # Mail to club also for the successful submission of the event
        mail_to_club = [
            mail_club,
        ]
        mail_subject_club = CLUB_EVENT_SUBJECT.safe_substitute(
            event_id=updated_event_instance.code,
            event=mail_event_title,
        )
        mail_body_club = SUBMIT_EVENT_BODY_FOR_CLUB.safe_substitute(
            event=mail_event_title,
            eventlink=mail_eventlink,
            event_id=updated_event_instance.code,
            club=clubname,
            description=mail_description,
            start_time=event_start_time,
            end_time=event_end_time,
            location=mail_location,
            poc_name=poc_name,
            poc_roll=poc_roll,
            poc_email=poc_email,
            poc_phone=poc_phone,
        )

        triggerMail(
            mail_uid,
            mail_subject_club,
            mail_body_club,
            toRecipients=mail_to_club,
            cookies=info.context.cookies,
        )
    if (
        updated_event_instance.status.state
        == Event_State_Status.pending_budget
    ):
        cc_to = getRoleEmails("cc")
        mail_to = getRoleEmails("slc")
    if updated_event_instance.status.state == Event_State_Status.pending_room:
        cc_to = getRoleEmails("cc")
        mail_to = getRoleEmails("slo")
        mail_body = PROGRESS_EVENT_BODY_FOR_SLO.safe_substitute(
            event_id=updated_event_instance.code,
            club=clubname,
            event=mail_event_title,
            description=mail_description,
            student_count=student_count,
            start_time=event_start_time,
            end_time=event_end_time,
            location=mail_location,
            equipment=equipment,
            budget=budget,
            additional=additional,
            poc_name=poc_name,
            poc_roll=poc_roll,
            poc_email=poc_email,
            poc_phone=poc_phone,
        )
    if updated_event_instance.status.state == Event_State_Status.approved:
        # mail to the club email
        mail_to = [
            mail_club,
        ]
        mail_subject = CLUB_EVENT_SUBJECT.safe_substitute(
            event_id=updated_event_instance.code,
            event=mail_event_title,
        )
        mail_body = APPROVED_EVENT_BODY_FOR_CLUB.safe_substitute(
            club=clubname,
            event=mail_event_title,
            eventlink=mail_eventlink,
        )

    if len(mail_to):
        triggerMail(
            mail_uid,
            mail_subject,
            mail_body,
            toRecipients=mail_to,
            ccRecipients=cc_to,
            cookies=info.context.cookies,
        )

    return EventType.from_pydantic(updated_event_instance)


@strawberry.mutation
def deleteEvent(eventid: str, info: Info) -> EventType:
    """
    change the state of the event to `deleted` if the user has permissions
    """
    user = info.context.user

    if user is None or user["role"] not in ["club", "cc", "slo"]:
        raise Exception("Not Authenticated!")

    query = {
        "_id": eventid,
    }
    if user["role"] not in ["cc", "slo"]:
        # if user is not an admin, they can only delete their own events
        query["clubid"] = user["uid"]

    updation = {
        "$set": {
            "status": {
                "state": Event_State_Status.deleted.value,
                "budget": False,
                "room": False,
            }
        }
    }

    old_ref = eventsdb.find_one(query)
    upd_ref = eventsdb.update_one(query, updation)
    if upd_ref.matched_count == 0:
        raise Exception(
            "Can not access event. Either it does not exist or user does not have perms."  # noqa: E501
        )

    # Send the event deleted email.
    old_event = Event.parse_obj(old_ref)
    if old_event.status.state not in [
        Event_State_Status.deleted,
        Event_State_Status.incomplete,
    ]:
        if user["role"] == "cc":
            mail_to = [
                getClubNameEmail(old_event.clubid, email=True, name=False),
            ]
            mail_subject = CLUB_EVENT_SUBJECT.safe_substitute(
                event_id=old_event.code,
                event=old_event.name,
            )
            mail_body = DELETE_EVENT_BODY_FOR_CLUB.safe_substitute(
                club=old_event.clubid,
                event=old_event.name,
                eventlink=getEventLink(old_event.code),
                deleted_by="Clubs Council",
            )
        if user["role"] == "slo":
            mail_to = [
                getClubNameEmail(old_event.clubid, email=True, name=False),
            ]
            mail_subject = CLUB_EVENT_SUBJECT.safe_substitute(
                event_id=old_event.code,
                event=old_event.name,
            )
            mail_body = DELETE_EVENT_BODY_FOR_CLUB.safe_substitute(
                club=old_event.clubid,
                event=old_event.name,
                eventlink=getEventLink(old_event.code),
                deleted_by="Student Life Office",
            )

            # Mail to CC for the deleted event
            mail_to_cc = getRoleEmails("cc")
            mail_subject_cc = PROGRESS_EVENT_SUBJECT.safe_substitute(
                event=old_event.name,
            )
            mail_body_cc = DELETE_EVENT_BODY_FOR_CC.safe_substitute(
                club="Student Life Office",
                event=old_event.name,
                eventlink=getEventLink(old_event.code),
            )

            triggerMail(
                user["uid"],
                mail_subject_cc,
                mail_body_cc,
                toRecipients=mail_to_cc,
                cookies=info.context.cookies,
            )

        elif user["role"] == "club":
            mail_to = getRoleEmails("cc")
            mail_subject = PROGRESS_EVENT_SUBJECT.safe_substitute(
                event=old_event.name,
            )
            mail_body = DELETE_EVENT_BODY_FOR_CC.safe_substitute(
                club=old_event.clubid,
                event=old_event.name,
                eventlink=getEventLink(old_event.code),
            )

        triggerMail(
            user["uid"],
            mail_subject,
            mail_body,
            toRecipients=mail_to,
            cookies=info.context.cookies,
        )

    upd_ref = eventsdb.find_one({"_id": eventid})
    return EventType.from_pydantic(Event.parse_obj(upd_ref))


@strawberry.mutation
def updateEventsCid(
    info: Info,
    old_cid: str,
    new_cid: str,
    inter_communication_secret: str | None = None,
) -> int:
    """
    update all events of old_cid to new_cid
    """
    user = info.context.user

    if user is None or user["role"] not in ["cc"]:
        raise Exception("Not Authenticated!")

    if inter_communication_secret != inter_communication_secret_global:
        raise Exception("Authentication Error! Invalid secret!")

    updation = {
        "$set": {
            "clubid": new_cid,
        }
    }

    upd_ref = eventsdb.update_many({"clubid": old_cid}, updation)
    return upd_ref.modified_count


# register all mutations
mutations = [
    createEvent,
    editEvent,
    progressEvent,
    deleteEvent,
    updateEventsCid,
]
