import strawberry
from datetime import timedelta
from pydantic import HttpUrl, parse_obj_as
from fastapi.encoders import jsonable_encoder

from db import eventsdb

# import all models and types
from models import Event
from otypes import Info, InputEventDetails, EventType, InputEditEventDetails
from mailing import triggerMail
from mtypes import (
    BudgetType,
    Event_Mode,
    Event_Location,
    Event_Full_Location,
    Audience,
    Event_State_Status,
)

from mailing_templates import (
    PROGRESS_EVENT_SUBJECT,
    PROGRESS_EVENT_BODY,
    PROGRESS_EVENT_BODY_FOR_SLO,
    CLUB_EVENT_SUBJECT,
    APPROVED_EVENT_BODY_FOR_CLUB,
    SUBMIT_EVENT_BODY_FOR_CLUB,
)
from utils import (
    getClubNameEmail,
    getEventCode,
    getEventLink,
    getMember,
    getRoleEmails,
    getUser,
)


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
        event_instance.location = [Event_Location(loc) for loc in details.location]
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
                    amount=x.amount, description=x.description, advance=x.advance
                ),
                details.budget,
            )
        )

    # Check POC Details Exist or not
    if not getMember(details.clubid, details.poc, cookies=info.context.cookies):
        raise Exception("Member Details for POC does not exist")

    # if creator is CC, set state to approved
    if user["role"] == "cc":
        event_instance.status.state = Event_State_Status.approved
        event_instance.status.budget = True
        event_instance.status.room = True

    # set event code
    event_instance.code = getEventCode(details.clubid, details.datetimeperiod[0])

    created_id = eventsdb.insert_one(jsonable_encoder(event_instance)).inserted_id
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
            raise Exception("Start datetime cannot be same/after end datetime.")

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
        and event_ref["status"]["state"] != Event_State_Status.incomplete
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
    if details.poc is not None and event_ref["poc"] != details.poc:
        updates["poc"] = details.poc
        # Check POC Details Exist or not
        if not getMember(details.clubid, details.poc, cookies=info.context.cookies):
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
                    amount=x.amount, description=x.description, advance=x.advance
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
    """
    noaccess_error = Exception(
        "Can not access event. Either it does not exist or user does not have perms."
    )

    user = info.context.user

    event_ref = eventsdb.find_one({"_id": eventid})
    if event_ref is None or user is None:
        raise noaccess_error
    event_instance = Event.parse_obj(event_ref)

    if event_instance.status.state == Event_State_Status.incomplete:
        if user["role"] != "club" or user["uid"] != event_instance.clubid:
            raise noaccess_error
        updation = {
            "budget": False,
            # or sum([b.amount for b in event_instance.budget]) == 0,
            "room": False,
            #   or len(event_instance.location) == 0,
            "state": Event_State_Status.pending_cc.value,
        }

    elif event_instance.status.state == Event_State_Status.pending_cc:
        if user["role"] != "cc":
            raise noaccess_error
        updation = {
            "budget": event_instance.status.budget,
            # or sum([b.amount for b in event_instance.budget]) == 0,
            "room": event_instance.status.room,
            #   or len(event_instance.location) == 0,
        }
        if cc_progress_budget is not None:
            updation["budget"] = cc_progress_budget
        if cc_progress_room is not None:
            updation["room"] = cc_progress_room

        if not updation["budget"]:
            updation["state"] = Event_State_Status.pending_budget.value
        elif not updation["room"]:
            updation["state"] = Event_State_Status.pending_room.value
        else:
            updation["state"] = Event_State_Status.approved.value

    elif event_instance.status.state == Event_State_Status.pending_budget:
        if user["role"] != "slc":
            raise noaccess_error
        assert event_instance.status.budget is False
        updation = {
            "budget": True,
            "room": event_instance.status.room,
            #   | len(event_instance.location) == 0,
        }

        if not updation["room"]:
            updation["state"] = Event_State_Status.pending_room.value
        else:
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
        }

    upd_ref = eventsdb.update_one({"_id": eventid}, {"$set": {"status": updation}})
    if upd_ref.matched_count == 0:
        raise noaccess_error

    event_ref = eventsdb.find_one({"_id": eventid})
    event = Event.parse_obj(event_ref)

    # trigger mail notification

    # Data Preparation for the mailing
    mail_uid = user["uid"]
    mail_club = getClubNameEmail(event.clubid, email=True)

    if mail_club is None:
        raise Exception("Club does not exist.")
    else:
        clubname, mail_club = mail_club
    
    mail_event_title = event.name
    mail_eventlink = getEventLink(event.code)
    mail_description = event.description
    if mail_description == "":
        mail_description = "N/A"
    
    student_count = event.population
    mail_location = ""
    if event.mode == Event_Mode.online:
        mail_location = "online"
        student_count = "N/A"
    else:
        mail_location = ", ".join(
            [getattr(Event_Full_Location, loc) for loc in event.location]
        )
    
    ist_offset = timedelta(hours=5, minutes=30)
    start_dt = event.datetimeperiod[0] + ist_offset
    end_dt = event.datetimeperiod[1] + ist_offset
    event_start_time = (
        str(start_dt.strftime("%d-%m-%Y")) + " " + str(start_dt.strftime("%H:%M"))
    )
    event_end_time = (
        str(end_dt.strftime("%d-%m-%Y")) + " " + str(end_dt.strftime("%H:%M"))
    )

    poc_details, poc_phone = getUser(event.poc, info.context.cookies)
    poc_name = poc_details["firstName"] + " " + poc_details["lastName"]
    poc_email = poc_details["email"]
    poc_roll = poc_details["rollno"]
    poc_phone = poc_phone["phone"]
    if not poc_phone:
        poc_phone = "Unknown"
    if not poc_roll:
        poc_roll = "Unknown"

    
    # Mail Subject and Body
    mail_subject = PROGRESS_EVENT_SUBJECT.safe_substitute(
        event=mail_event_title,
    )
    mail_body = PROGRESS_EVENT_BODY.safe_substitute(
        club=clubname,
        event=mail_event_title,
        eventlink=mail_eventlink,
    )

    if event.status.state == Event_State_Status.pending_room:
        mail_body = PROGRESS_EVENT_BODY_FOR_SLO.safe_substitute(
            event_id=event.code,
            club=clubname,
            event=mail_event_title,
            description=mail_description,
            student_count=student_count,
            start_time=event_start_time,
            end_time=event_end_time,
            location=mail_location,
            poc_name=poc_name,
            poc_roll=poc_roll,
            poc_email=poc_email,
            poc_phone=poc_phone,
        )

    mail_to = []
    if event.status.state == Event_State_Status.pending_cc:
        mail_to = getRoleEmails("cc")

        # Mail to club also for the successful submission of the event
        mail_to_club = [
            mail_club,
        ]
        mail_subject_club = CLUB_EVENT_SUBJECT.safe_substitute(
            event_id=event.code,
            event=mail_event_title,
        )
        mail_body_club = SUBMIT_EVENT_BODY_FOR_CLUB.safe_substitute(
            event=mail_event_title,
            eventlink=mail_eventlink,
            event_id=event.code,
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
    if event.status.state == Event_State_Status.pending_budget:
        mail_to = getRoleEmails("slc")
    if event.status.state == Event_State_Status.pending_room:
        mail_to = getRoleEmails("slo")
    if event.status.state == Event_State_Status.approved:
        # mail to the club email
        mail_to = [
            mail_club,
        ]
        mail_subject = CLUB_EVENT_SUBJECT.safe_substitute(
            event_id=event.code,
            event=mail_event_title,
        )
        mail_body = APPROVED_EVENT_BODY_FOR_CLUB.safe_substitute(
            event=mail_event_title,
            eventlink=mail_eventlink,
        )

    if len(mail_to):
        triggerMail(
            mail_uid,
            mail_subject,
            mail_body,
            toRecipients=mail_to,
            cookies=info.context.cookies,
        )

    return EventType.from_pydantic(event)


@strawberry.mutation
def deleteEvent(eventid: str, info: Info) -> EventType:
    """
    change the state of the event to `deleted` if the user has permissions
    """
    user = info.context.user

    if user is None or user["role"] not in ["club", "cc"]:
        raise Exception("Not Authenticated!")

    query = {
        "_id": eventid,
    }
    if user["role"] not in ["cc"]:
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

    upd_ref = eventsdb.update_one(query, updation)
    if upd_ref.matched_count == 0:
        raise Exception(
            "Can not access event. Either it does not exist or user does not have perms."
        )

    event_ref = eventsdb.find_one({"_id": eventid})
    return EventType.from_pydantic(Event.parse_obj(event_ref))


# register all mutations
mutations = [
    createEvent,
    editEvent,
    progressEvent,
    deleteEvent,
]
