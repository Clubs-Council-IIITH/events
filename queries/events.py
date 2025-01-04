"""
Query Resolvers for Events

This file contains the query resolvers for the events service.

resolvers:
    event: Fetches an event with the given id
    events: Fetches all events
    eventid: Fetches an event id with the given event code
    incompleteEvents: Fetches incomplete events of clubs
    pendingEvents: Fetches pending events of clubs
    availableRooms: Fetches available rooms for a given date and time
    downloadEventsData: Fetches all events as a CSVResponse
"""

import csv
import io
from typing import Any, List

import dateutil.parser as dp
import strawberry

from db import eventsdb

# import all models and types
from models import Event
from mtypes import (
    Event_Full_Location,
    Event_Full_State_Status,
    Event_Location,
    Event_State_Status,
)
from otypes import (
    CSVResponse,
    EventType,
    Info,
    InputDataReportDetails,
    RoomList,
    RoomListType,
    timelot_type,
)
from utils import eventsWithSorting, getClubs, trim_public_events


@strawberry.field
def event(eventid: str, info: Info) -> EventType:
    """
    Fetches an event with the given id

    This method is used to fetch an event with the given event id.

    Inputs:
        eventid (str): The id of the event to be fetched.
        info (Info): The context information of user for the request.

    Returns:
        EventType: Details regarding The event with the given id.

    Accessibility:
        fully accessibile to only cc, slo and slc and also the club in question itself.
        partial access to public as it hides few fields of information.

    Raises Exception:
        Cannot access event: If the user is not autherized to access the event.
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
                        or (
                            user["uid"] != event["clubid"]
                            and (
                                event["collabclubs"]
                                and user["uid"] not in event["collabclubs"]
                            )
                        )
                    )
                )
            )
        )
        or event["clubid"] not in list_allclubs
    ):
        raise Exception(
            "Can not access event. Either it does not exist or user does not have perms."  # noqa: E501
        )

    if (
        user is None
        or user["role"] not in ["club", "cc", "slc", "slo"]
        or (user["role"] == "club" and user["uid"] != event["clubid"])
    ):
        trim_public_events(event)

    return EventType.from_pydantic(Event.model_validate(event))


@strawberry.field
def eventid(code: str, info: Info) -> str:
    """
    method returns eventid of the event with the given event code

    Inputs:
        code (str): The code of the event to be fetched.
        info (Info): The context information of user for the request.

    Returns:
        str: The id of the event with the given code.

    Raises Exception:
        Event with given code does not exist : If the event with the given code does not exist.
    """

    event = eventsdb.find_one({"code": code})

    if event is None:
        raise Exception("Event with given code does not exist.")

    return event["_id"]


@strawberry.field
def events(
    info: Info,
    clubid: str | None = None,
    name: str | None = None,
    public: bool | None = None,
    paginationOn: bool = False,
    limit: int | None = None,
    skip: int = 0,
) -> List[EventType]:
    """
    Returns a list of events as a search result that match the given criteria.

    This method is used to fetch a list of events as a search result that match the given criteria.
    If public is set to True, then only public/approved events are returned.
    If clubid is set, then only events of that club are returned.
    If clubid is not set, then all events the user is authorized to see are returned.
    not logged in user has same visibility as public set to True.
    If public set to True, then few fields of the evnt are hidden using the trim_public_events function.

    Inputs:
        info (Info): The context information of user for the request.
        clubid (str | None): The id of the club whose events are to be fetched.
        name (str | None): The name of the event to be searched according to.
        public (bool | None): Whether to return only public events.
        paginationOn (bool): Whether to use pagination.
        limit (int | None): The maximum number of events to return.
        skip (int): The number of events to skip.

    Returns:
        List[EventType]: A list of events that match the given criteria.

    Accessibility:
        fully accessibile to only cc, slo and slc and also the club in question itself.
        partial access to public as it hides few fields of information.

    Raises Exception:
        Pagination limit is required: If paginationOn is True and limit is not provided.        
    """

    user = info.context.user

    restrictAccess = True
    clubAccess = False
    restrictFullAccess = True
    if user is not None and (public is None or public is False):
        if user["role"] in ["cc", "slc", "slo"]:
            restrictAccess = False
            if user["role"] in [
                "cc",
            ]:
                restrictFullAccess = False

        if user["role"] == "club":
            clubAccess = True
            restrictAccess = False
            if user["uid"] == clubid:
                restrictFullAccess = False

    assert not (
        restrictAccess and not restrictFullAccess
    ), "restrictAccess and not restrictFullAccess can not be True at the same time."  # noqa: E501

    if not limit and paginationOn:
        raise Exception("Pagination limit is required.")

    searchspace: dict[str, Any] = {}
    if clubid is not None:
        searchspace["$or"] = [
            {"clubid": clubid},
            {"collabclubs": {"$in": [clubid]}},
        ]
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
    elif restrictFullAccess:
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

    events = eventsWithSorting(
        searchspace,
        date_filter=False,
        pagination=paginationOn,
        name=name,
        skip=skip,
        limit=limit,
    )

    # hides few fields from public viewers
    if restrictAccess or public:
        for event in events:
            trim_public_events(event)

    return [
        EventType.from_pydantic(Event.model_validate(event))
        for event in events
    ]


@strawberry.field
def incompleteEvents(clubid: str, info: Info) -> List[EventType]:
    """
    Return all incomplete events of a club
    
    This method is used to return all 'incomplete' state evts of a given club.
    
    Inputs:
        clubid (str): The id of the club whose incomplete events are to be fetched.
        info (Info): The context information of user for the request.

    Returns:
        List[EventType]: A list of events that match the given criteria.

    Accessibility:
        Only to the club itself.

    Raises Exception:
        You do not have permission to access this resource : If the user is not a club or does not have permission to access the resource.
    """
    user = info.context.user

    if not user or user["role"] != "club" or user["uid"] != clubid:
        raise Exception("You do not have permission to access this resource.")

    events = eventsdb.find(
        {
            "$or": [{"clubid": clubid}, {"collabclubs": {"$in": [clubid]}}],
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
        EventType.from_pydantic(Event.model_validate(event))
        for event in events
    ]


# @strawberry.field
# def approvedEvents(clubid: str | None, info: Info) -> List[EventType]:
#     """
#     if clubid is set, return approved events of that club.
#     else return approved events of every club.
#     NOTE: this is a public query, accessible to all.
#     """

#     requested_state = Event_State_Status.approved.value

#     searchspace = {
#         "status.state": requested_state,
#     }
#     if clubid is not None:
#         searchspace["$or"] = [
#             {"clubid": clubid},
#             {"collabclubs": {"$in": [clubid]}},
#         ]
#     else:
#         allclubs = getClubs(info.context.cookies)
#         list_allclubs = list()
#         for club in allclubs:
#             list_allclubs.append(club["cid"])
#         searchspace["clubid"] = {"$in": list_allclubs}

#     searchspace["audience"] = {"$nin": ["internal"]}

#     events = eventsdb.find(searchspace)

#     # sort events in descending order of time
#     events = sorted(
#         events,
#         key=lambda event: event["datetimeperiod"][0],
#         reverse=True,
#     )

#     TODO: Add trimming of events as public events

#     return [
#         EventType.from_pydantic(Event.model_validate(event)) for event in events
#     ]


@strawberry.field
def pendingEvents(clubid: str | None, info: Info) -> List[EventType]:
    """
    Returns all the pending events of a give club id

    This method is used to return all 'pending' state events of a given club.
    For CC, returns events with pending approval from CC. Same for SLO and SLC.
    For club, returns incomplete and pending approval events.
    It sorts them on the basis of time.

    Inputs:
        clubid (str): The id of the club whose pending events are to be fetched.
        info (Info): The context information of user for the request.

    Returns:
        List[EventType]: A list of events that match the given criteria.

    Accessibility:
        Only to the club, CC, SLO, SLC.

    Raises Exception:
            You do not have permission to access this resource : If the user is not a club or does not have permission to access the resource.
    """

    user = info.context.user

    requested_states: set[str] = set()
    searchspace: dict[str, Any] = {}
    if user is not None:
        if "cc" == user["role"]:
            requested_states |= {Event_State_Status.pending_cc.value}
        if "slc" == user["role"]:
            requested_states |= {Event_State_Status.pending_budget.value}
        if "slo" == user["role"]:
            requested_states |= {Event_State_Status.pending_room.value}
            searchspace["$or"] = [
                {"status.budget": True},
                {"studentBodyEvent": True},
            ]
        if "club" == user["role"] and user["uid"] == clubid:
            requested_states |= {
                Event_State_Status.incomplete.value,
                Event_State_Status.pending_cc.value,
                Event_State_Status.pending_budget.value,
                Event_State_Status.pending_room.value,
            }

    if user is None or len(requested_states) == 0:
        raise Exception("You do not have permission to access this resource.")

    searchspace["status.state"] = {
        "$in": list(requested_states),
    }
    if clubid is not None:
        if "$or" not in searchspace:
            searchspace["$or"] = [
                {"clubid": clubid},
                {"collabclubs": {"$in": [clubid]}},
            ]
        else:
            old_or = searchspace["$or"]
            del searchspace["$or"]
            searchspace["$and"] = [
                {"$or": old_or},
                {
                    "$or": [
                        {"clubid": clubid},
                        {"collabclubs": {"$in": [clubid]}},
                    ]
                },
            ]

    events = eventsdb.find(searchspace)

    # simply sorts events in ascending order of time
    events = sorted(
        events,
        key=lambda event: event["datetimeperiod"][0],
        reverse=False,
    )

    return [
        EventType.from_pydantic(Event.model_validate(event))
        for event in events
    ]


@strawberry.field
def availableRooms(
    timeslot: timelot_type, eventid: str | None, info: Info
) -> RoomListType:
    """
    return a list of all rooms that are available in the given timeslot
    
    This method is used to return all the rooms that are available in the given timeslot.
    To the returned list it add the current location of the event whose event id is also provided.
    A room is considered not available if an approved event has booked that room in that timeslot.

    Inputs:
        timeslot (timelot_type): The timeslot for which the rooms are to be fetched.
        eventid (str): The id of the event whose location is to be added to the list of rooms.
        info (Info): The context information of user for the request.

    Returns:
        RoomListType: A list of rooms that are available in the given timeslot.

    Accessibility:
        Public(The user need tobe logged in to access this resource)

    Raises Exception:
        You do not have permission to access this resource : If the user is not logged in or is SLC.
    """
    user = info.context.user

    if user is None or user["role"] not in ["club", "cc", "slo"]:
        raise Exception("You do not have permission to access this resource.")

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

    free_rooms = set(Event_Location.__members__.values())
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
        RoomList.model_validate({"locations": free_rooms})
    )


@strawberry.field
def downloadEventsData(
    details: InputDataReportDetails, info: Info
) -> CSVResponse:
    """
    Returns all the events as a CSVResponse according to the details provided.

    This function is similar to the events method, but it returns all the events as a CSVResponse.
    It sends specific set of events on the basis of the details provided.
    If clubid is provided, it returns all the events of that club.
    If status is provided, it returns all the events with that status.
    If a time frame is provided, it returns all the events happening in that time frame.
    It returns info regarding each event, which will contain the fields provided in the details.

    Inputs:
        details (InputDataReportDetails): The details of the events to be fetched.
        info (Info): The context information of user for the request.

    Returns:
        CSVResponse: A CSVResponse containing all the events.

    Accessibility:
        CC and SLO cannot see deleted and incomplete events.Public can see only approved events.

    Raises Exception:
        You do not have permission to access this resource : If the user is not autherized to access the resource.
        Invalid status : If the status provided is not valid.
    """
    user = info.context.user
    if user is None:
        raise Exception("You do not have permission to access this resource.")

    if details.status not in ["pending", "approved", "all"]:
        raise Exception("Invalid status")

    all_events = list()
    allclubs = getClubs(info.context.cookies)
    searchspace: dict[str, Any] = {}

    if details.clubid:
        clubid = details.clubid
        if details.clubid == "allclubs":
            clubid = None
        if user is not None:
            if clubid is not None:
                searchspace["$or"] = [
                    {"clubid": clubid},
                    {"collabclubs": {"$in": [clubid]}},
                ]
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

            if (
                user["role"] not in ["cc", "slo"]
                or details.status == "approved"
            ):
                searchspace["status.state"] = {
                    "$in": [
                        Event_State_Status.approved.value,
                    ]
                }
            else:
                to_exclude = [
                    Event_State_Status.deleted.value,
                    Event_State_Status.incomplete.value,
                ]
                if details.status == "pending":
                    to_exclude.append(Event_State_Status.approved.value)
                if user["role"] == "slo":
                    to_exclude.append(Event_State_Status.pending_cc.value)
                searchspace["status.state"] = {
                    "$nin": to_exclude,
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
        "status": "Status",
        "equipment": "Equipment",
        "additional": "Additional Requests",
    }

    # Prepare CSV content
    csv_output = io.StringIO()
    fieldnames = [
        header_mapping.get(field.lower(), field)
        for field in details.fields
        if field != "status"
    ]

    if details.status != "approved":
        fieldnames.append(header_mapping["status"])

    csv_writer = csv.DictWriter(csv_output, fieldnames=fieldnames)
    csv_writer.writeheader()

    for event in all_events:
        event_data = {}
        for field in details.fields:
            mapped_field = header_mapping.get(field, field)
            if mapped_field not in fieldnames:
                continue

            value = event.get(field)

            if field in ["datetimeperiod.0", "datetimeperiod.1"]:
                value = event.get("datetimeperiod")
                value = (
                    value[0].split("T")[0]
                    if field == "datetimeperiod.0"
                    else value[1].split("T")[0]
                )
            elif field == "clubid":
                value = next(
                    (
                        club["name"]
                        for club in allclubs
                        if club["cid"] == value
                    ),
                    "",
                )
            elif field == "location":
                value = event.get(field, [])
                if len(value) >= 1:
                    value = ", ".join(
                        getattr(Event_Full_Location, loc) for loc in value
                    )
            elif field == "budget":
                if isinstance(value, list):
                    budget_items = [
                        f"{item['description']} {'(Advance)' if item['advance'] else ''}: {item['amount']}"  # noqa: E501
                        for item in value
                    ]
                    value = ", ".join(budget_items)
            elif field == "status":
                status_value = event.get(field, {})
                value = status_value.get("state", None)

                if value:
                    value = getattr(Event_Full_State_Status, value)

            if value in [None, "", []]:
                value = "No " + mapped_field

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
    # approvedEvents,
    pendingEvents,
    availableRooms,
    downloadEventsData,
]
