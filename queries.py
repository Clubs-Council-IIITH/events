import csv
import io
from typing import List

import dateutil.parser as dp
import strawberry

from db import eventsdb

# import all models and types
from models import Event
from mtypes import Event_Full_Location, Event_Location, Event_State_Status
from otypes import (
    CSVResponse,
    EventType,
    Info,
    InputReportDetails,
    RoomList,
    RoomListType,
    timelot_type,
)
from utils import eventsWithSorting, getClubs


@strawberry.field
def event(eventid: str, info: Info) -> EventType:
    """
    return event with given id if it is visible to the user
    """
    user = info.context.user
    event = eventsdb.find_one({"_id": eventid})

    allclubs = getClubs(info.context.cookies)
    list_allclubs = list()
    for club in allclubs:
        list_allclubs.append(club["cid"])

    if (
        event is None
        or (
            event["status"]["state"]
            not in {
                Event_State_Status.approved.value,
            }
            and (
                user is None
                or (
                    user["role"] not in {"cc", "slc", "slo"}
                    and (
                        user["role"] != "club"
                        or user["uid"] != event["clubid"]
                    )
                )
            )
        )
        or event["clubid"] not in list_allclubs
    ):
        raise Exception(
            "Can not access event. Either it does not exist or user does not have perms."  # noqa: E501
        )

    return EventType.from_pydantic(Event.parse_obj(event))


@strawberry.field
def eventid(code: str, info: Info) -> str:
    """
    return eventid given event code
    """

    event = eventsdb.find_one({"code": code})

    if event is None:
        raise Exception("Event with given code does not exist.")

    return event["_id"]


@strawberry.field
def events(
    info: Info,
    clubid: str | None,
    public: bool | None,
    limit: int | None = None,
) -> List[EventType]:
    """
    if public is set, then return only public/approved events
    else
        return all events visible to the user
        if clubid is specified, then return events of that club only
    """
    user = info.context.user

    restrictAccess = True
    clubAccess = False
    restrictCCAccess = True
    if user is not None and (public is None or public is False):
        if user["role"] in ["cc", "slc", "slo"]:
            restrictAccess = False
            if user["role"] in [
                "cc",
            ]:
                restrictCCAccess = False

        if user["role"] == "club":
            clubAccess = True
            restrictAccess = False
            if user["uid"] == clubid:
                restrictCCAccess = False

    assert not (
        restrictAccess and not restrictCCAccess
    ), "restrictAccess and not restrictCCAccess can not be True at the same time."  # noqa: E501

    searchspace = dict()
    if clubid is not None:
        searchspace["clubid"] = clubid
    else:
        allclubs = getClubs(info.context.cookies)
        list_allclubs = list()
        for club in allclubs:
            list_allclubs.append(club["cid"])
        searchspace["clubid"] = {"$in": list_allclubs}
    if restrictAccess:
        searchspace["status.state"] = {
            "$in": [
                Event_State_Status.approved.value,
            ]
        }
        searchspace["audience"] = {"$nin": ["internal"]}
    elif restrictCCAccess:
        statuses = [
            Event_State_Status.approved.value,
            Event_State_Status.pending_budget.value,
            Event_State_Status.pending_room.value,
        ]
        if clubAccess:
            searchspace["audience"] = {"$nin": ["internal"]}
            statuses.append(Event_State_Status.pending_cc.value)
            statuses.append(Event_State_Status.incomplete.value)

        searchspace["status.state"] = {
            "$in": statuses,
        }

    events = eventsWithSorting(searchspace, date_filter=False)

    if limit is not None:
        events = events[:limit]

    return [
        EventType.from_pydantic(Event.parse_obj(event)) for event in events
    ]


@strawberry.field
def incompleteEvents(clubid: str, info: Info) -> List[EventType]:
    """
    return all incomplete events of a club
    raise Exception if user is not a member of the club
    """
    user = info.context.user

    if not user or user["role"] != "club" or user["uid"] != clubid:
        raise Exception("You do not have permission to access this resource.")

    events = eventsdb.find(
        {
            "clubid": clubid,
            "status.state": Event_State_Status.incomplete.value,
        }
    )

    # sort events in ascending order of time
    events = sorted(
        events,
        key=lambda event: event["datetimeperiod"][0],
        reverse=False,
    )

    return [
        EventType.from_pydantic(Event.parse_obj(event)) for event in events
    ]


@strawberry.field
def approvedEvents(clubid: str | None, info: Info) -> List[EventType]:
    """
    if clubid is set, return approved events of that club.
    else return approved events of every club.
    NOTE: this is a public query, accessible to all.
    """

    requested_state = Event_State_Status.approved.value

    searchspace = {
        "status.state": requested_state,
    }
    if clubid is not None:
        searchspace["clubid"] = clubid
    else:
        allclubs = getClubs(info.context.cookies)
        list_allclubs = list()
        for club in allclubs:
            list_allclubs.append(club["cid"])
        searchspace["clubid"] = {"$in": list_allclubs}

    searchspace["audience"] = {"$nin": ["internal"]}

    events = eventsdb.find(searchspace)

    # sort events in descending order of time
    events = sorted(
        events,
        key=lambda event: event["datetimeperiod"][0],
        reverse=True,
    )

    return [
        EventType.from_pydantic(Event.parse_obj(event)) for event in events
    ]


@strawberry.field
def pendingEvents(clubid: str | None, info: Info) -> List[EventType]:
    """
    if user is admin, return events pending for them
    if InpClub is set, and current user belongs to that club,
    return pending events of that club.
    raise Exception if user is not adimn and user is not in that club.
    """
    user = info.context.user

    requested_states = set()
    searchspace = dict()
    if user is not None:
        if "cc" == user["role"]:
            requested_states |= {Event_State_Status.pending_cc.value}
        if "slc" == user["role"]:
            requested_states |= {Event_State_Status.pending_budget.value}
        if "slo" == user["role"]:
            requested_states |= {Event_State_Status.pending_room.value}
            searchspace["status.budget"] = True
        if "club" == user["role"] and user["uid"] == clubid:
            requested_states |= {
                Event_State_Status.incomplete.value,
                Event_State_Status.pending_cc.value,
                Event_State_Status.pending_budget.value,
                Event_State_Status.pending_room.value,
            }
    requested_states = list(requested_states)

    if user is None or len(requested_states) == 0:
        raise Exception("You do not have permission to access this resource.")

    searchspace["status.state"] = {
        "$in": requested_states,
    }
    if clubid is not None:
        searchspace["clubid"] = clubid

    events = eventsdb.find(searchspace)

    # sort events in ascending order of time
    events = sorted(
        events,
        key=lambda event: event["datetimeperiod"][0],
        reverse=False,
    )

    return [
        EventType.from_pydantic(Event.parse_obj(event)) for event in events
    ]


@strawberry.field
def availableRooms(
    timeslot: timelot_type, eventid: str | None, info: Info
) -> RoomListType:
    """
    return a list of all rooms that are available in the given timeslot
    NOTE: this is a public query, accessible to all.
    """
    assert timeslot[0] < timeslot[1], "Invalid timeslot"

    approved_events = eventsdb.find(
        {
            "status.state": Event_State_Status.approved.value,
        },
        {
            "location": 1,
            "datetimeperiod": 1,
        },
    )

    free_rooms = set(Event_Location)
    for approved_event in approved_events:
        start_time = dp.parse(approved_event["datetimeperiod"][0])
        end_time = dp.parse(approved_event["datetimeperiod"][1])
        if timeslot[1] >= start_time and timeslot[0] <= end_time:
            free_rooms.difference_update(approved_event["location"])

    if eventid is not None:
        event = eventsdb.find_one({"_id": eventid})
        if event is not None:
            free_rooms.update(event["location"])

    return RoomListType.from_pydantic(
        RoomList.parse_obj({"locations": free_rooms})
    )


@strawberry.field
def downloadEventsData(details: InputReportDetails, info: Info) -> CSVResponse:
    """
    Create events data in CSV format for the events with
    given details in the given date period.
    """
    user = info.context.user
    all_events = list()

    allclubs = getClubs(info.context.cookies)
    searchspace = dict()
    if details.clubid:
        clubid = details.clubid
        if details.clubid == "allclubs":
            clubid = None
        if user is not None:
            if clubid is not None:
                searchspace["clubid"] = clubid
            else:
                list_allclubs = [club["cid"] for club in allclubs]
                searchspace["clubid"] = {"$in": list_allclubs}

            # filter by date
            if details.dateperiod:
                datetime_start = details.dateperiod[0].strftime(
                    "%Y-%m-%dT00:00:00+00:00"
                )
                datetime_end = details.dateperiod[1].strftime(
                    "%Y-%m-%dT23:59:59+00:00"
                )
                searchspace["datetimeperiod.0"] = {
                    "$gte": datetime_start,
                    "$lte": datetime_end,
                }

            # include only approved events
            searchspace["status.state"] = {
                "$in": [
                    Event_State_Status.approved.value,
                ]
            }

            all_events = eventsWithSorting(searchspace, date_filter=True)

    header_mapping = {
        "code": "Event Code",
        "name": "Event Name",
        "clubid": "Club",
        "datetimeperiod.0": "StartDate",
        "datetimeperiod.1": "EndDate",
        "description": "Description",
        "audience": "Audience",
        "population": "Audience Count",
        "mode": "Mode",
        "location": "Venue",
        "budget": "Budget",
        "poster": "Poster URL",
    }

    # Prepare CSV content
    csv_output = io.StringIO()
    fieldnames = [
        header_mapping.get(field.lower(), field) for field in details.fields
    ]

    csv_writer = csv.DictWriter(csv_output, fieldnames=fieldnames)
    csv_writer.writeheader()

    for event in all_events:
        event_data = {}
        for field in details.fields:
            mapped_field = header_mapping.get(field, field)
            value = event.get(field)

            if field in ["datetimeperiod.0", "datetimeperiod.1"]:
                value = event.get("datetimeperiod")
                value = (
                    value[0].split("T")[0]
                    if field == "datetimeperiod.0"
                    else value[1].split("T")[0]
                )
            if value in [None, "", []]:
                event_data[mapped_field] = "No " + mapped_field
            elif field == "clubid":
                event_data[mapped_field] = next(
                    (
                        club["name"]
                        for club in allclubs
                        if club["cid"] == value
                    ),
                    "",
                )
            elif field == "location":
                if value == []:
                    event_data[mapped_field] = "No location"
                else:
                    event_data[mapped_field] = ", ".join(
                        getattr(Event_Full_Location, loc) for loc in value
                    )
                    event_data[mapped_field] = f"{event_data[mapped_field]}"
            else:
                event_data[mapped_field] = value
        csv_writer.writerow(event_data)

    csv_content = csv_output.getvalue()
    csv_output.close()
    return CSVResponse(
        csvFile=csv_content,
        successMessage="CSV file generated successfully",
        errorMessage="",
    )


# register all queries
queries = [
    event,
    events,
    eventid,
    incompleteEvents,
    approvedEvents,
    pendingEvents,
    availableRooms,
    downloadEventsData,
]
