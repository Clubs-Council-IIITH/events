import json
from datetime import date, datetime
from functools import cached_property
from typing import Dict, List, Optional, Tuple, TypeAlias

import strawberry
from graphql import GraphQLError
from pydantic import BaseModel, TypeAdapter, ValidationError
from strawberry.fastapi import BaseContext
from strawberry.types import Info as _Info
from strawberry.types.info import RootValueType

from models import Event, EventReport, Holiday
from mtypes import (
    Audience,
    Bills_State_Status,
    Bills_Status,
    BudgetType,
    Event_Location,
    Event_Mode,
    PyObjectId,
    SponsorType,
    event_popu_type,
    medium_str_type,
    short_str_type,
    very_short_str_type,
)


# custom context class
class Context(BaseContext):
    """
    Class provides user metadata and cookies from request headers, has
    methods for doing this.
    """

    @cached_property
    def user(self) -> Dict | None:
        if not self.request:
            return None
        user = json.loads(self.request.headers.get("user", "{}"))
        return user

    @cached_property
    def cookies(self) -> Dict | None:
        if not self.request:
            return None

        cookies = json.loads(self.request.headers.get("cookies", "{}"))
        return cookies


Info: TypeAlias = _Info[Context, RootValueType]
"""custom info Type for user metadata"""


PyObjectIdType = strawberry.scalar(
    PyObjectId, serialize=str, parse_value=lambda v: PyObjectId(v)
)
"""A scalar Type for serializing PyObjectId, used for id field"""


@strawberry.experimental.pydantic.type(model=EventReport, all_fields=True)
class EventReportType:
    """
    Type for returning the event's report.
    """

    pass


@strawberry.experimental.pydantic.type(model=Event, all_fields=True)
class EventType:
    """
    Type for returning all the details regarding an event.
    """

    pass


@strawberry.type
class RoomInfo:
    """
    Class for returning the location and availability of a room.

    Attributes:
        location (mtypes.Event_Location): The location of the room.
        available (bool): Whether the room is available or not.
    """

    location: Event_Location
    available: bool


@strawberry.type
class RoomListType:
    """
    Type for returning a list of locations with the availability

    Attributes:
        locations (List[mtypes.RoomInfo]): List of locations with availability.
    """

    locations: List[RoomInfo]


@strawberry.type
class BillsStatusType:
    """
    Type for returning event id, event name, club id and bills status of
    the event.

    Attributes:
        eventid (str): ID of the event.
        eventname (mtypes.very_short_str_type): Name of the event.
        clubid (str): ID of the club organizing the event.
        bills_status (mtypes.Bills_Status): Bills status of the event.
        eventReportSubmitted (mtypes.short_str_type): Status of event report.
    """

    eventid: str
    eventname: str
    clubid: str
    bills_status: Bills_Status
    eventReportSubmitted: str


@strawberry.type
class CSVResponse:
    """
    Type for returning the csv file, success/error message.

    Attributes:
        csvFile (mtypes.short_str_type): The csv file as a string.
        successMessage (mtypes.short_str_type): The success message.
        errorMessage (mtypes.short_str_type): The error message.
    """

    csvFile: str
    successMessage: str
    errorMessage: str


# EVENT INPUTS


@strawberry.input
class BudgetInput(BudgetType):
    """
    Input for taking all fields of the BudgetType class.
    """

    pass


@strawberry.input
class SponsorInput(SponsorType):
    """
    Input for taking all fields of the SponsorType class.
    """

    pass


class InputEventDetailsBaseModel(BaseModel):
    """
    Base Model Class for taking the details of an event.

    Attributes:
        name (mtypes.very_short_str_type): Name of the event.
        location (List[mtypes.Event_Location]): List of locations of the event.
                                         Default is None.
        otherLocation (mtypes.very_short_str_type): 'Other' location of the event.
                                             Default is None.
        locationAlternate (List[mtypes.Event_Location]): List of alternate locations
                                                  of the event.Default is None.
        otherLocationAlternate (mtypes.very_short_str_type): 'Other' alternate location
                                                     of the event. Default is None.
        description (mtypes.medium_str_type): Description of the event. Default is None.
        clubid (str): clubID of the club organizing the event.
        collabclubs (List[str]): List of clubIDs of collaborating clubs.
                                 Default is None.
        mode (mtypes.Event_Mode): Mode of the event. Default is hybrid.
        poster (str): Poster of the event. Default is None.
        datetimeperiod (List[datetime]): List of date and time of start and
                                         end of the event.
        audience (List[mtypes.Audience]): List of audience categories for the event.
                                   Default is None.
        link (mtypes.HttpUrlString): Link to the event. Default is None.
        equipment (mtypes.short_str_type): Equipment for the event. Default is None.
        additional (mtypes.short_str_type): Additional information of the event.
                                    Default is None.
        population (mtypes.event_popu_type): Population expected to attend the event.
                                     Default is None.
        external_population (Optional[mtypes.event_popu_type]): Population expected
                                    from outside attending the event.
        budget (List[BudgetInput]): List of budgets of the event.
                                    Default is None.
        sponsor (List[SponsorInput]): List of sponsor of the event.
                                    Default is None.
        poc (str): Point of contact for the event.
    """  # noqa: E501

    name: very_short_str_type
    location: List[Event_Location] | None = None
    otherLocation: very_short_str_type | None = None  # very_short_str_type
    locationAlternate: List[Event_Location] | None = None
    otherLocationAlternate: very_short_str_type | None = (
        None  # very_short_str_type
    )
    description: medium_str_type | None = None
    clubid: str
    collabclubs: List[str] | None = None
    mode: Event_Mode | None = Event_Mode.hybrid
    poster: str | None = None
    datetimeperiod: List[datetime]
    audience: List[Audience] | None = None
    link: str | None = None
    equipment: short_str_type | None = None
    additional: short_str_type | None = None
    population: event_popu_type | None = None
    external_population: Optional[event_popu_type] = None
    budget: List[BudgetInput] | None = None
    sponsor: List[SponsorInput] | None = None
    poc: str


@strawberry.experimental.pydantic.input(
    model=InputEventDetailsBaseModel, all_fields=True
)
class InputEventDetails:
    """
    Input for taking all fields of the InputEventDetailsBaseModel class.
    """

    pass


class InputEditEventDetailsBaseModel(BaseModel):
    """
    Input similar to InputEventDetailsBaseModel but along with the event
    id(self-generated) attribute.

    Attributes:
        name (mtypes.very_short_str_type): Name of the event. Default is None.
        eventid (str): ID of the event.
        collabclubs (List[str]): List of clubIDs of collaborating clubs.
                                 Default is None.
        location (List[mtypes.Event_Location]): List of locations of the event.
                                         Default is None.
        otherLocation (mtypes.very_short_str_type): 'Other' location
                                    of the event.Default is None.
        locationAlternate (List[mtypes.Event_Location]): List of alternate
                                                  locations of the event.
                                                    Default is None.
        otherLocationAlternate (mtypes.very_short_str_type): 'Other' alternate
                                                      location of the event.
                                                     Default is None.
        description (mtypes.medium_str_type): Description of the event.
                                            Default is None.
        clubid (str): clubID of the club organizing the event. Default is None.
        mode (mtypes.Event_Mode): Mode of the event.Default is hybrid.
        poster (str): Poster of the event. Default is None.
        datetimeperiod (List[datetime]): List of date and time of start and
                                         end of the event. Default is None.
        audience (List[mtypes.Audience]): List of audience
                                        categories for the event.
                                   Default is None.
        link (mtypes.HttpUrlString): Link to the event. Default is None.
        equipment (mtypes.short_str_type): Equipment for the event.
                                         Default is None.
        additional (mtypes.short_str_type): Additional information of event.
                                    Default is None.
        population (mtypes.event_popu_type): Population
                                         expected to attend the event.
                                     Default is None.
        external_population (Optional[mtypes.event_popu_type]): Population
                                                         expected from outside
                                                         attending the event.
        budget (List[BudgetInput]): List of budgets for the event.
                                    Default is None.
        sponsor (List[SponsorInput]): List of sponsors for the event.
                                    Default is None.
        poc (str): Point of contact for the event. Default is None.
    """

    name: very_short_str_type | None = None
    eventid: str
    collabclubs: List[str] | None = None
    location: List[Event_Location] | None = None
    otherLocation: very_short_str_type | None = None
    locationAlternate: List[Event_Location] | None = None
    otherLocationAlternate: very_short_str_type | None = None
    description: medium_str_type | None = None
    clubid: str | None
    mode: Event_Mode | None = Event_Mode.hybrid
    poster: str | None = None
    datetimeperiod: List[datetime] | None = None
    audience: List[Audience] | None = None
    link: str | None = None
    equipment: short_str_type | None = None
    additional: short_str_type | None = None
    population: event_popu_type | None = None
    external_population: Optional[event_popu_type] = None
    budget: List[BudgetInput] | None = None
    sponsor: List[SponsorInput] | None = None
    poc: str | None = None


@strawberry.experimental.pydantic.input(
    model=InputEditEventDetailsBaseModel, all_fields=True
)
class InputEditEventDetails:
    """
    Input for taking all fields of the InputEditEventDetailsBaseModel class.
    """

    pass


@strawberry.input
class InputDataReportDetails:
    """
    Input used for taking info required to bring a list of events along
    with required fields.

    Attributes:
        clubid (str | None): ID of the club. Default is None.
        dateperiod (List[date] | None): List of dates for filtering events.
                                       Default is None.
        fields (List[mtypes.short_str_type]): List of fields in the response.
        status (mtypes.short_str_type): Status of the event.
    """

    clubid: str | None
    dateperiod: List[date] | None = None
    fields: List[str]
    status: str


@strawberry.experimental.pydantic.input(model=EventReport, all_fields=True)
class InputEventReport:
    """
    Input for taking all the fields of the EventReport model.
    """

    pass


@strawberry.input
class InputBillsStatus:
    """
    Input for taking event id, state of the bill and slo comment during
    the approval/rejection of bills.

    Attributes:
        eventid (str): ID of the event.
        state (mtypes.Bills_State_Status): State of the bill.
        slo_comment (mtypes.short_str_type): Comment of SLO. Default is None.
    """

    eventid: str
    state: Bills_State_Status
    slo_comment: str | None = None  # short_str_type

    def __post_init__(self):
        if self.slo_comment is not None:
            try:
                short_str_type_adapter = TypeAdapter(short_str_type)
                self.slo_comment = short_str_type_adapter.validate_python(
                    self.slo_comment
                )
            except ValidationError as e:
                raise GraphQLError(
                    f"Invalid slo_comment: {e.errors()[0]['msg']}"
                )


@strawberry.input
class InputBillsUpload:
    """
    Input for taking event id, and filename of the bill generated by
    getSignedUploadURL function.

    Attributes:
        eventid (str): ID of the event.
        filename (mtypes.very_short_str_type): Filename of the bill.
        budget (List[BudgetInput]): List of budgets for the event.
    """

    eventid: str
    filename: str  # very_short_str_type
    budget: List[BudgetInput]

    def __post_init__(self):
        try:
            very_short_str_type_adapter = TypeAdapter(very_short_str_type)
            self.filename = very_short_str_type_adapter.validate_python(
                self.filename
            )
        except ValidationError as e:
            raise GraphQLError(f"Invalid filename: {e.errors()[0]['msg']}")


# custom data type for start and end of event
timelot_type = Tuple[datetime, datetime]
"""A custom data type for start and end of event"""

# Holidays Types


@strawberry.input
class InputHolidayDetails:
    """
    Input for taking the details of a holiday.

    Attributes:
        date (date): Date of the holiday.
        name (mtypes.very_short_str_type): Name of the holiday.
        description (mtypes.medium_str_type): Description of the holiday.
                                      Default is None.
    """

    date: date
    name: str  # very_short_str_type
    description: str | None = None  # medium_str_type

    def __post_init__(self):
        try:
            very_short_str_type_adapter = TypeAdapter(very_short_str_type)
            self.name = very_short_str_type_adapter.validate_python(self.name)
        except ValidationError as e:
            raise GraphQLError(f"Invalid name: {e.errors()[0]['msg']}")

        if self.description is not None:
            medium_str_type_adapter = TypeAdapter(medium_str_type)
            try:
                self.description = medium_str_type_adapter.validate_python(
                    self.description
                )
            except ValidationError as e:
                raise GraphQLError(
                    f"Invalid description: {e.errors()[0]['msg']}"
                )


@strawberry.experimental.pydantic.type(model=Holiday, all_fields=True)
class HolidayType:
    """
    Type for returning all the details regarding a holiday.
    """

    pass
