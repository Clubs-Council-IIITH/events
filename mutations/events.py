"""
Mutation Resolvers

initially, the event is `incomplete`
after the club fills all the details, they progress it
cc chooses to progress the state status, the budget status and the room status
if budget status is unapproved, the event is `pending_budget`, else skip to next
after budget is approved (through any track),
if room status is unapproved, the event is `pending_room`, else skip to next
after room is approved (through any track), the event is `approved`
once the event is over, the club or cc can change the state to `completed`
"""  # noqa: E501

import os
from datetime import datetime, timedelta

import strawberry
from fastapi.encoders import jsonable_encoder
from prettytable import PrettyTable

from db import eventsdb
from mailing import triggerMail
from mailing_templates import (
    APPROVED_EVENT_BODY_FOR_CLUB,
    CLUB_EVENT_SUBJECT,
    DELETE_EVENT_BODY_FOR_CC,
    DELETE_EVENT_BODY_FOR_CLUB,
    DELETE_EVENT_SUBJECT,
    PROGRESS_EVENT_BODY,
    PROGRESS_EVENT_BODY_FOR_SLC,
    PROGRESS_EVENT_BODY_FOR_SLO,
    PROGRESS_EVENT_SUBJECT,
    REJECT_EVENT_BODY_FOR_CLUB,
    REJECT_EVENT_SUBJECT,
    SUBMIT_EVENT_BODY_FOR_CLUB,
)

# import all models and types
from models import Event
from mtypes import (
    Audience,
    BudgetType,
    ClubBodyCategoryType,
    Event_Full_Location,
    Event_Location,
    Event_Mode,
    Event_State_Status,
    SponsorType,
    timezone,
)
from otypes import EventType, Info, InputEditEventDetails, InputEventDetails
from utils import (
    delete_file,
    getClubDetails,
    getEventCode,
    getEventLink,
    getMember,
    getRoleEmails,
    getUser,
)

inter_communication_secret_global = os.getenv("INTER_COMMUNICATION_SECRET")
noaccess_error = Exception(
    "Can not access event. Either it does not exist or user does not have perms."  # noqa: E501
)


@strawberry.mutation
async def createEvent(details: InputEventDetails, info: Info) -> EventType:
    """
    Method to create an event by a club,CC.

    Args:
        details (InputEventDetails): The details of the event to be created.
        info (Info): The context of the request for user info.

    Returns:
        (EventType): returns all details regarding the event created.

    Raises:
        Exception: You do not have permission to access this resource.
        Exception: Start time cannot be after end time.
        Exception: Club does not exist.
        Exception: Member details of POC does not exist.
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

    # Check if the club exists
    club_details = await getClubDetails(details.clubid, info.context.cookies)
    if len(club_details.keys()) == 0:
        raise Exception("Club does not exist.")

    event_instance = Event(
        name=details.name.strip(),
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
    if details.locationAlternate is not None:
        event_instance.locationAlternate = [
            Event_Location(loc) for loc in details.locationAlternate
        ]
    if details.otherLocation is not None and "other" in details.location:
        event_instance.otherLocation = details.otherLocation
    if details.otherLocationAlternate is not None and "other" in details.locationAlternate:
        event_instance.otherLocationAlternate = details.otherLocationAlternate
    if details.description is not None:
        event_instance.description = details.description.strip()
    if details.poster is not None:
        event_instance.poster = details.poster
    if details.audience is not None:
        event_instance.audience = [Audience(aud) for aud in details.audience]
    if details.link is not None:
        event_instance.link = details.link
    if details.equipment is not None:
        event_instance.equipment = details.equipment
    if details.additional is not None:
        event_instance.additional = details.additional
    if details.population is not None:
        event_instance.population = details.population
    if (
        details.external_population is not None
        and details.external_population > 0
    ):
        # External popluation should be lower than internal
        if (
            details.population
            and details.population < details.external_population
        ):
            raise Exception(
                "Number of external participants should be less than total."
            )
        event_instance.external_population = details.external_population
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
    if details.sponsor is not None:
        event_instance.sponsor = list(
            map(
                lambda x: SponsorType(
                    name=x.name,
                    website=x.website if x.website else "None",
                    amount=x.amount,
                    previously_sponsored=x.previously_sponsored,
                ),
                details.sponsor,
            )
        )
    if details.collabclubs and details.collabclubs != []:
        event_instance.collabclubs = details.collabclubs

    # Check POC Details Exist or not
    if not await getMember(
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

    # get current time
    current_time = datetime.now(timezone)
    time_str = current_time.strftime("%d-%m-%Y %I:%M %p")
    event_instance.status.last_updated_time = time_str
    event_instance.status.last_updated_by = user["uid"]

    # generates and sets the event's code
    event_instance.code = await getEventCode(
        details.clubid, details.datetimeperiod[0]
    )

    if club_details["category"] == "body":
        event_instance.club_category = ClubBodyCategoryType.body
    elif club_details["category"] == "admin":
        event_instance.club_category = ClubBodyCategoryType.admin
    else:
        event_instance.club_category = ClubBodyCategoryType.club

    created_id = (
        await eventsdb.insert_one(jsonable_encoder(event_instance))
    ).inserted_id
    created_event = Event.model_validate(
        await eventsdb.find_one({"_id": created_id})
    )

    return EventType.from_pydantic(created_event)


@strawberry.mutation
async def editEvent(details: InputEditEventDetails, info: Info) -> EventType:
    """
    Method used to edit an event by a club,CC,SLO

    It approves the event if the edit is being performed by the CC and set the approver to the user.
    It also updates the last updated time and last updated by fields.
    It does not remove previous approvals.

    Args:
        details (InputEditEventDetails): The details of the event to be edited.
        info (Info): The context of the request for user info.

    Returns:
        (EventType): The edited event.

    Raises:
        Exception: Not Authenticated!
        Exception: Not Authenticated to access this API
        Exception: Start datetime cannot be same/after end datetime.
        Exception: Event does not exist.
        Exception: Member Details for POC does not exist
        Exception: You do not have permission to access this resource.
    """  # noqa: E501
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

    event_ref = await eventsdb.find_one({"_id": details.eventid})
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
        "status.last_updated_time": datetime.now(timezone).strftime(
            "%d-%m-%Y %I:%M %p"
        ),
        "status.last_updated_by": user["uid"],
    }

    updatable = user["role"] in allowed_roles or (
        user["role"] == "club"
        and event_ref["status"]["state"] == Event_State_Status.incomplete
    )

    if details.name is not None and updatable:
        updates["name"] = details.name.strip()
    if details.datetimeperiod is not None and updatable:
        updates["datetimeperiod"] = details.datetimeperiod
    if details.mode is not None and updatable:
        updates["mode"] = Event_Mode(details.mode)
    if details.location is not None and updatable:
        # updates["status.room"] = False or user["role"] == "cc"
        updates["location"] = [Event_Location(loc) for loc in details.location]
    if details.locationAlternate is not None and updatable:
        updates["locationAlternate"] = [
            Event_Location(loc) for loc in details.locationAlternate
        ]
    if details.otherLocation is not None and updatable and "other" in details.otherLocation:
        updates["otherLocation"] = details.otherLocation
    if details.otherLocationAlternate is not None and updatable and "other" in details.otherLocationAlternate:
        updates["otherLocationAlternate"] = details.otherLocationAlternate
    if details.collabclubs is not None and updatable:
        updates["collabclubs"] = details.collabclubs
    if details.poc is not None and event_ref.get("poc", None) != details.poc:
        updates["poc"] = details.poc
        # Check POC Details Exist or not
        if not await getMember(
            details.clubid, details.poc, cookies=info.context.cookies
        ):
            raise Exception("Member Details for POC does not exist")
    if details.description is not None:
        updates["description"] = details.description.strip()
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
    if (
        details.external_population is not None
        and details.external_population > 0
    ):
        if (
            details.population
            and details.population < details.external_population
        ):
            raise Exception(
                "Number of external participants should be less than total."
            )
        updates["external_population"] = details.external_population

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
    if details.sponsor is not None:
        updates["sponsor"] = list(
            map(
                lambda x: SponsorType(
                    name=x.name,
                    website=x.website if x.website else "None",
                    amount=x.amount,
                    previously_sponsored=x.previously_sponsored,
                ),
                details.sponsor,
            )
        )

    old_poster_file = event_ref.get("poster", None)
    if details.poster is not None:
        updates["poster"] = details.poster
        if old_poster_file and old_poster_file == details.poster:
            old_poster_file = None

    query = {
        "_id": details.eventid,
        "clubid": user["uid"]
        if (user is not None and user["role"] == "club")
        else details.clubid
        if (user["role"] in allowed_roles)
        else None,
    }

    updation = {"$set": jsonable_encoder(updates)}

    upd_ref = await eventsdb.update_one(query, updation)
    if upd_ref.matched_count == 0:
        raise Exception("You do not have permission to access this resource.")

    if old_poster_file:
        try:
            await delete_file(old_poster_file)
        except Exception as e:
            print(f"Error deleting poster file {old_poster_file}\nError: {e}")
    event_ref = await eventsdb.find_one({"_id": details.eventid})
    return EventType.from_pydantic(Event.model_validate(event_ref))


@strawberry.mutation
async def progressEvent(
    eventid: str,
    info: Info,
    cc_progress_budget: bool | None = None,
    cc_progress_room: bool | None = None,
    cc_approver: str | None = None,
    slc_members_for_email: list[str] | None = None,
) -> EventType:
    """
    progress the event state status for different users

    Args:
        eventid (str): event id
        info (Info): info object
        cc_progress_budget (bool | None, optional): progress budget. Defaults to None.
        cc_progress_room (bool | None, optional): progress room. Defaults to None.
        cc_approver (str | None, optional): cc approver. Defaults to None.
        slc_members_for_email (list[str] | None, optional): list of SLC members for email. Defaults to None.

    Returns:
        (EventType): event object

    Raises:
        Exception: Club does not exist.
        Exception: CC Approver is required to progress event.
        Exception: POC does not exist.
    """  # noqa: E501

    user = info.context.user

    event_ref = await eventsdb.find_one({"_id": eventid})
    if event_ref is None or user is None:
        raise noaccess_error
    event_instance = Event.model_validate(event_ref)

    mail_uid = user["uid"]
    clubDetails = await getClubDetails(
        event_instance.clubid, info.context.cookies
    )
    if len(clubDetails.keys()) == 0:
        raise Exception("Club does not exist.")
    else:
        mail_club = clubDetails["email"]
        clubname = clubDetails["name"]

    # get current time
    current_time = datetime.now(timezone)
    time_str = current_time.strftime("%d-%m-%Y %I:%M %p")

    is_admin = event_instance.club_category == ClubBodyCategoryType.admin
    is_body = event_instance.club_category == ClubBodyCategoryType.body

    if event_instance.status.state == Event_State_Status.incomplete:
        if user["role"] != "club" or user["uid"] != event_instance.clubid:
            raise noaccess_error
        new_state = Event_State_Status.pending_cc.value
        if is_body:
            new_state = Event_State_Status.pending_room.value
        elif is_admin:
            new_state = Event_State_Status.approved.value

        updation = {
            "budget": is_admin,
            # or sum([b.amount for b in event_instance.budget]) == 0,
            "room": is_admin,
            #   or len(event_instance.location) == 0,
            "state": new_state,
            "cc_approver": None,
            "slc_approver": None,
            "slo_approver": user["uid"] if is_admin else None,
            "submission_time": time_str,
            "cc_approver_time": "Not Approved",
            "slc_approver_time": "Not Approved",
            "slo_approver_time": time_str if is_admin else "Not Approved",
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
        assert event_instance.status.budget or is_body
        assert event_instance.status.room is False
        updation = {
            "budget": event_instance.status.budget or is_body,
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

    # Unchanged Values
    updation["last_updated_time"] = event_instance.status.last_updated_time
    updation["last_updated_by"] = event_instance.status.last_updated_by
    updation["deleted_time"] = event_instance.status.deleted_time
    updation["deleted_by"] = event_instance.status.deleted_by

    poc = await getUser(event_instance.poc, info.context.cookies)
    if not poc:
        raise Exception("POC does not exist.")

    upd_ref = await eventsdb.update_one(
        {"_id": eventid}, {"$set": {"status": updation}}
    )
    if upd_ref.matched_count == 0:
        raise noaccess_error

    event_ref = await eventsdb.find_one({"_id": eventid})
    updated_event_instance = Event.model_validate(event_ref)

    ## trigger mail notification
    # Data Preparation for the mailing
    mail_event_title = updated_event_instance.name
    mail_eventlink = getEventLink(updated_event_instance.code)
    mail_description = updated_event_instance.description
    if mail_description == "":
        mail_description = "N/A"

    student_count = updated_event_instance.population

    mail_location = ""
    mail_locationAlternate = ""
    if updated_event_instance.mode == Event_Mode.online:
        mail_location = "online"
        mail_locationAlternate = "N/A"
    else:
        mail_location = ", ".join(
            [
                getattr(Event_Full_Location, loc, None)
                if loc != "other"
                else (updated_event_instance.otherLocation or "other")
                for loc in updated_event_instance.location
            ]
        )
        mail_locationAlternate = ", ".join(
            [
                getattr(Event_Full_Location, loc, None)
                if loc != "other"
                else (updated_event_instance.otherLocationAlternate or "other")
                for loc in updated_event_instance.locationAlternate
            ]
        )

    # handle external participants
    external_count = updated_event_instance.external_population
    if external_count and external_count > 0:
        student_count = (
            str(student_count + external_count)
            + f" (External Participants: {external_count})"
        )

    equipment, additional, budget, sponsor = "N/A", "N/A", "N/A", "N/A"
    if updated_event_instance.equipment:
        equipment = updated_event_instance.equipment
    if updated_event_instance.additional:
        additional = updated_event_instance.additional
    if updated_event_instance.budget:
        budget_table = PrettyTable()
        budget_table.field_names = ["Description", "Amount", "Advance"]
        for item in updated_event_instance.budget:
            budget_table.add_row(
                [
                    item.description,
                    item.amount,
                    "Yes" if item.advance else "No",
                ],
                divider=True,
            )
        total_budget = sum(
            item.amount for item in updated_event_instance.budget
        )
        budget_table.add_row(["Total budget", total_budget, ""], divider=True)
        budget_table.max_width["Description"] = 20
        budget_table.max_width["Amount"] = 8
        budget_table.max_width["Advance"] = 7
        budget_table.align["Amount"] = "r"

        budget = "\n" + budget_table.get_string()

    if updated_event_instance.sponsor:
        sponsor_table = PrettyTable()
        sponsor_table.field_names = [
            "Name",
            "Website",
            "Amount",
            "Previously Sponsored",
        ]
        for item in updated_event_instance.sponsor:
            sponsor_table.add_row(
                [
                    item.name,
                    item.website,
                    item.amount,
                    "Yes" if item.previously_sponsored else "No",
                ],
                divider=True,
            )
        total_sponsor = sum(
            item.amount for item in updated_event_instance.sponsor
        )
        sponsor_table.add_row(
            ["", "Total sponsor", total_sponsor, ""], divider=True
        )
        sponsor_table.max_width["Name"] = 10
        sponsor_table.max_width["Website"] = 20
        sponsor_table.max_width["Amount"] = 8
        sponsor_table.max_width["Previously Sponsored"] = 5
        sponsor_table.align["Amount"] = "r"

        sponsor = "\n" + sponsor_table.get_string()

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
        mail_to = await getRoleEmails("cc")

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
            locationAlternate=mail_locationAlternate,
            budget=budget,
            sponsor=sponsor,
            poc_name=poc_name,
            poc_roll=poc_roll,
            poc_email=poc_email,
            poc_phone=poc_phone,
        )

        await triggerMail(
            mail_uid,
            mail_subject_club,
            mail_body_club,
            toRecipients=mail_to_club,
            ccRecipients=[poc_email],
            cookies=info.context.cookies,
        )
    elif (
        updated_event_instance.status.state
        == Event_State_Status.pending_budget
    ):
        cc_to = await getRoleEmails("cc") + await getRoleEmails("slo")
        slc_emails = await getRoleEmails("slc")

        if slc_members_for_email is not None:
            mail_to = []
            for email in slc_emails:
                if email.split("@")[0] in slc_members_for_email:
                    mail_to.append(email)
        else:
            mail_to = slc_emails
        mail_body = PROGRESS_EVENT_BODY_FOR_SLC.safe_substitute(
            event_id=updated_event_instance.code,
            club=clubname,
            event=mail_event_title,
            description=mail_description,
            start_time=event_start_time,
            end_time=event_end_time,
            student_count=student_count,
            location=mail_location,
            locationAlternate=mail_locationAlternate,
            budget=budget,
            sponsor=sponsor,
            additional=additional,
            eventlink=mail_eventlink,
        )
    elif (
        updated_event_instance.status.state == Event_State_Status.pending_room
    ):
        cc_to = await getRoleEmails("cc") + ([mail_club] if is_body else [])
        mail_to = await getRoleEmails("slo")
        mail_body = PROGRESS_EVENT_BODY_FOR_SLO.safe_substitute(
            event_id=updated_event_instance.code,
            club=clubname,
            event=mail_event_title,
            description=mail_description,
            student_count=student_count,
            start_time=event_start_time,
            end_time=event_end_time,
            location=mail_location,
            locationAlternate=mail_locationAlternate,
            equipment=equipment,
            budget=budget,
            sponsor=sponsor,
            additional=additional,
            poc_name=poc_name,
            poc_roll=poc_roll,
            poc_email=poc_email,
            poc_phone=poc_phone,
        )
    elif updated_event_instance.status.state == Event_State_Status.approved:
        # mail to the club email
        mail_to = [
            mail_club,
        ]
        cc_to = [poc_email]
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
        await triggerMail(
            mail_uid,
            mail_subject,
            mail_body,
            toRecipients=mail_to,
            ccRecipients=cc_to,
            cookies=info.context.cookies,
        )
    return EventType.from_pydantic(updated_event_instance)


@strawberry.mutation
async def deleteEvent(eventid: str, info: Info) -> EventType:
    """
    change the state of an event to `deleted` by CC, SLO or club, also triggers emails to concerned parties

    Args:
        eventid (str): The ID of the event to be deleted.
        info (Info): The context of the request for user info.

    Returns:
        (EventType): The state set to deleted event.

    Raises:
        Exception: Not Authenticated!
        Exception: Club does not exist.
    """  # noqa: E501
    user = info.context.user

    if user is None or user["role"] not in ["club", "cc", "slo"]:
        raise Exception("Not Authenticated!")

    query = {
        "_id": eventid,
    }
    if user["role"] not in ["cc", "slo"]:
        # if user is not an admin, they can only delete their own events
        query["clubid"] = user["uid"]

    event_ref = await eventsdb.find_one(query)
    if event_ref is None:
        raise noaccess_error
    event_instance = Event.model_validate(event_ref)

    updation = event_ref["status"]
    updation["state"] = Event_State_Status.deleted.value
    updation["budget"] = False
    updation["room"] = False
    updation["deleted_by"] = user["uid"]
    updation["deleted_time"] = datetime.now(timezone).strftime(
        "%d-%m-%Y %I:%M %p"
    )

    clubDetails = await getClubDetails(
        event_instance.clubid, info.context.cookies
    )
    if len(clubDetails.keys()) == 0:
        raise Exception("Club does not exist.")
    else:
        mail_club = clubDetails["email"]
        clubname = clubDetails["name"]

    event_ref = await eventsdb.update_one(
        query, {"$set": {"status": updation}}
    )
    if event_ref.matched_count == 0:
        raise noaccess_error

    # Send the event deleted email.
    if event_instance.status.state not in [
        Event_State_Status.deleted,
        Event_State_Status.incomplete,
    ]:
        if user["role"] == "cc":
            mail_to = [
                mail_club,
            ]
            mail_subject = DELETE_EVENT_SUBJECT.safe_substitute(
                event_id=event_instance.code,
                event=event_instance.name,
            )
            mail_body = DELETE_EVENT_BODY_FOR_CLUB.safe_substitute(
                club=clubname,
                event=event_instance.name,
                eventlink=getEventLink(event_instance.code),
                deleted_by="Clubs Council",
            )
        elif user["role"] == "slo":
            mail_to = [
                mail_club,
            ]
            cc_to = await getRoleEmails("cc")
            mail_subject = DELETE_EVENT_SUBJECT.safe_substitute(
                event_id=event_instance.code,
                event=event_instance.name,
            )
            mail_body = DELETE_EVENT_BODY_FOR_CLUB.safe_substitute(
                club=clubname,
                event=event_instance.name,
                eventlink=getEventLink(event_instance.code),
                deleted_by="Student Life Office",
            )

            await triggerMail(
                user["uid"],
                mail_subject,
                mail_body,
                toRecipients=mail_to,
                ccRecipients=cc_to,
                cookies=info.context.cookies,
            )
        elif user["role"] == "club":
            mail_to = await getRoleEmails("cc")
            mail_subject = DELETE_EVENT_SUBJECT.safe_substitute(
                event_id=event_instance.code,
                event=event_instance.name,
            )
            mail_body = DELETE_EVENT_BODY_FOR_CC.safe_substitute(
                club=clubname,
                event=event_instance.name,
                eventlink=getEventLink(event_instance.code),
            )

            await triggerMail(
                user["uid"],
                mail_subject,
                mail_body,
                toRecipients=mail_to,
                cookies=info.context.cookies,
            )

    event_ref = await eventsdb.find_one({"_id": eventid})
    return EventType.from_pydantic(Event.model_validate(event_ref))


@strawberry.mutation
async def rejectEvent(
    eventid: str,
    reason: str,
    info: Info,
) -> EventType:
    """
    Reject Event by CC and reset the state to incomplete, triggers emails to club and cc.

    Args:
        eventid (str): The event id of the evnt that is being rejected.
        reason (str): The reason for rejection.
        info (Info): The context of the request for user info.

    Returns:
        (EventType): The event that was rejected.

    Raises:
        Exception: Not Authenticated!
        Exception: Club does not exist.
        Exception: Cannot reset event that has progressed beyond CC.
    """  # noqa: E501
    user = info.context.user

    if user is None or user["role"] != "cc":
        raise Exception("Not Authenticated!")

    query = {
        "_id": eventid,
    }

    event_ref = await eventsdb.find_one(query)
    if event_ref is None:
        raise noaccess_error

    event_instance = Event.model_validate(event_ref)

    clubDetails = await getClubDetails(
        event_instance.clubid, info.context.cookies
    )
    if len(clubDetails.keys()) == 0:
        raise Exception("Club does not exist.")
    else:
        mail_club = clubDetails["email"]
        clubname = clubDetails["name"]

    if event_instance.status.state != Event_State_Status.pending_cc:
        raise Exception("Cannot reset event that has progressed beyond CC.")

    status = event_instance.model_dump()["status"]
    status["state"] = Event_State_Status.incomplete.value
    status["budget"] = False
    status["room"] = False
    status["submission_time"] = None

    upd_ref = await eventsdb.update_one(
        {"_id": eventid}, {"$set": {"status": status}}
    )
    if upd_ref.matched_count == 0:
        raise noaccess_error

    # Send email to Club for allowing edits
    mail_to = [mail_club]
    mail_subject = REJECT_EVENT_SUBJECT.safe_substitute(
        event_id=event_instance.code,
        event=event_instance.name,
    )
    mail_body = REJECT_EVENT_BODY_FOR_CLUB.safe_substitute(
        club=clubname,
        event=event_instance.name,
        eventlink=getEventLink(event_instance.code),
        reason=reason,
        deleted_by="Clubs Council",
    )

    # Mail to the club regarding the rejected event
    await triggerMail(
        user["uid"],
        mail_subject,
        mail_body,
        toRecipients=mail_to,
        cookies=info.context.cookies,
    )

    return EventType.from_pydantic(Event.model_validate(event_ref))


@strawberry.mutation
async def updateEventsCid(
    info: Info,
    old_cid: str,
    new_cid: str,
    inter_communication_secret: str | None = None,
) -> int:
    """
    update all events of old_cid to new_cid by CC.

    Args:
        old_cid: old cid of the club
        new_cid: new cid of the club
        inter_communication_secret: secret for authentication. Default is None.

    Returns:
        (int): number of events updated

    Raises:
        Exception: Not Authenticated!
        Exception: Authentication Error! Invalid secret!
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

    upd_ref = await eventsdb.update_many({"clubid": old_cid}, updation)
    return upd_ref.modified_count


# register all mutations
mutations = [
    createEvent,
    editEvent,
    progressEvent,
    deleteEvent,
    rejectEvent,
    updateEventsCid,
]
