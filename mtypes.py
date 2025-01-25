from enum import StrEnum, auto

import pytz
import strawberry
from bson import ObjectId
from pydantic import (
    BeforeValidator,
    Field,
    HttpUrl,
    StringConstraints,
    TypeAdapter,
    field_validator,
)
from pydantic_core import core_schema
from typing_extensions import Annotated, Any


# Audience for the Event
@strawberry.enum
class Audience(StrEnum):
    """
    Enum for catagory of audience
    """

    ug1 = auto()
    ug2 = auto()
    ug3 = auto()
    ug4 = auto()
    pg = auto()
    stf = auto()
    fac = auto()
    internal = auto()


# Event Bills States
@strawberry.enum
class Bills_State_Status(StrEnum):
    """
    Enum of status of an event's bills
    """

    # initially, the bills are `not_submitted`
    not_submitted = auto()
    # after the club submits the bills, but they are incomplete,
    # the state is `incomplete`
    incomplete = auto()
    # after the club submits the bills, and they are complete,
    # the state is `submitted`
    submitted = auto()
    # SLO have processed the bills, the state is `slo_processed`
    slo_processed = auto()


# Event Bills State Full Names
class Bills_Full_State_Status:
    """
    String representation of the states in Bills_State_Status
    """

    not_submitted = "Not Submitted"
    incomplete = "Incomplete"
    submitted = "Submitted"
    slo_processed = "Processed by SLO"


# Event Bills Status
@strawberry.type
class Bills_Status:
    """
    Class used for a bill's approval/rejection status along with its time and
    comment on approval/rejection

    Attributes:
        state (Bills_State_Status): State of the bills. Initially, the bills
        are `not_submitted`.
        updated_time (str | None): Time of approval/rejection. Defaults 
                                   to None.
        slo_comment (str | None): Comment of SLO. Defaults to None.
    """

    state: Bills_State_Status = Bills_State_Status.not_submitted
    updated_time: str | None = None
    slo_comment: str | None = None

    def __init__(
        self,
        state: Bills_State_Status = Bills_State_Status.not_submitted,
        updated_time: str | None = None,
        slo_comment: str | None = None,
    ):
        self.state = state
        self.updated_time = updated_time
        self.slo_comment = slo_comment


# Event States
@strawberry.enum
class Event_State_Status(StrEnum):
    """
    Enum for state of an event's approval
    """

    # initially, the event is `incomplete`
    incomplete = auto()
    # after the club fills all the details, they progress it
    pending_cc = auto()
    # cc chooses to progress the state status, the budget status and the room status # noqa: E501
    # if budget status is unapproved, the event is `pending_budget`, else skip to next  # noqa: E501
    pending_budget = auto()
    # after budget is approved (through any track),
    # if room status is unapproved, the event is `pending_room`, else skip to next # noqa: E501
    pending_room = auto()
    # after room is approved (through any track), the event is `approved`
    approved = auto()
    # if the event is deleted, its state is `deleted`
    deleted = auto()


# Event Full State Names
class Event_Full_State_Status:
    """
    String representation of the states in Event_State_Status
    """

    incomplete = "Incomplete"
    pending_cc = "Pending CC Approval"
    pending_budget = "Pending Budget Approval"
    pending_room = "Pending Room Approval"
    approved = "Approved"
    deleted = "Deleted"


# Event Status
@strawberry.type
class Event_Status:
    """
    Class used for an event's approval status and approver information

    Attributes:
        state (Event_State_Status): State of the event. Default is `incomplete`.
        room (bool): Whether or not room is approved.
        budget (bool): Whether or not budget is approved.
        submission_time (str | None): Time of submission. Defaults to None.
        cc_approver (str | None): Approver of CC. Defaults to None.
        cc_approver_time (str | None): Time of approval by CC. 
                                       Defaults to None.
        slo_approver (str | None): Approver of SLO. Defaults to None.
        slo_approver_time (str | None): Time of approval by SLO. 
                                        Defaults to None.
        slc_approver (str | None): Approver of SLC. Defaults to None.
        slc_approver_time (str | None): Time of approval by SLC. 
                                        Defaults to None.
        last_updated_by (str | None): Last updated by. Defaults to None.
        last_updated_time (str | None): Time of last update. Defaults to None.
        deleted_by (str | None): Deleted by. Defaults to None.
        deleted_time (str | None): Time of deletion. Defaults to None.
    """

    state: Event_State_Status = Event_State_Status.incomplete
    room: bool = False
    budget: bool = False

    submission_time: str | None = None

    cc_approver: str | None = None
    cc_approver_time: str | None = None

    slo_approver: str | None = None
    slo_approver_time: str | None = None

    slc_approver: str | None = None
    slc_approver_time: str | None = None

    last_updated_by: str | None = None
    last_updated_time: str | None = None

    deleted_by: str | None = None
    deleted_time: str | None = None

    def __init__(
        self,
        state: Event_State_Status = Event_State_Status.incomplete,  # type: ignore
        room: bool = False,
        budget: bool = False,
        submission_time: str | None = None,
        cc_approver: str | None = None,
        cc_approver_time: str | None = None,
        slo_approver: str | None = None,
        slo_approver_time: str | None = None,
        slc_approver: str | None = None,
        slc_approver_time: str | None = None,
        last_updated_by: str | None = None,
        last_updated_time: str | None = None,
        deleted_by: str | None = None,
        deleted_time: str | None = None,
    ):
        self.state = state
        self.room = room
        self.budget = budget

        self.submission_time = submission_time

        self.cc_approver = cc_approver
        self.cc_approver_time = cc_approver_time

        self.slo_approver = slo_approver
        self.slo_approver_time = slo_approver_time

        self.slc_approver = slc_approver
        self.slc_approver_time = slc_approver_time

        self.last_updated_by = last_updated_by
        self.last_updated_time = last_updated_time

        self.deleted_by = deleted_by
        self.deleted_time = deleted_time


# Event Modes
@strawberry.enum
class Event_Mode(StrEnum):
    """
    Enum for mode of Event
    """

    hybrid = auto()
    online = auto()
    offline = auto()


# Event Full Location Names
class Event_Full_Location:
    """
    String representation of the locations in Event_Location
    """

    h101 = "Himalaya 101"
    h102 = "Himalaya 102"
    h103 = "Himalaya 103"
    h104 = "Himalaya 104"
    h201 = "Himalaya 201"
    h202 = "Himalaya 202"
    h203 = "Himalaya 203"
    h204 = "Himalaya 204"
    h301 = "Himalaya 301"
    h302 = "Himalaya 302"
    h303 = "Himalaya 303"
    h304 = "Himalaya 304"
    va3_117 = "Vindhya A3 117"
    vsh1 = "Vindhya SH1"
    vsh2 = "Vindhya SH2"
    amphi = "Amphitheatre"
    warehouse = "Bakul Warehouse"
    felig = "Felicity Ground"
    footg = "Football Ground"
    guest = "Guest House"
    cieg = "CIE Gaming"
    sarg = "Saranga Hall"
    h105 = "Himalaya 105"
    h205 = "Himalaya 205"
    krba = "KRB Auditorium"
    lm22 = "LM-22, KRB"
    sm24 = "SM-24, KRB"
    sm32 = "SM-32, KRB"
    lm34 = "LM-34, KRB"
    d101 = "D101, T-Hub"
    other = "Other"


# Event Locations
@strawberry.enum
class Event_Location(StrEnum):
    """
    Enum for locations for the Event
    """

    # Himalaya
    h101 = auto()
    h102 = auto()
    h103 = auto()
    h104 = auto()
    h201 = auto()
    h202 = auto()
    h203 = auto()
    h204 = auto()
    h301 = auto()
    h302 = auto()
    h303 = auto()
    h304 = auto()
    # Vindhya
    va3_117 = auto()
    vsh1 = auto()
    vsh2 = auto()
    # Other
    amphi = auto()
    warehouse = auto()
    cieg = auto()
    sarg = auto()
    felig = auto()
    footg = auto()
    guest = auto()
    # Academic Rooms
    h105 = auto()
    h205 = auto()
    # KRB
    krba = auto()
    lm22 = auto()
    sm24 = auto()
    sm32 = auto()
    lm34 = auto()
    # T-Hub
    d101 = auto()
    # nota
    other = auto()


event_popu_type = Annotated[int, Field(ge=0)]

very_short_str_type = Annotated[
    str, StringConstraints(min_length=1, max_length=200)
]
short_str_type = Annotated[str, StringConstraints(max_length=1000)]
medium_str_type = Annotated[str, StringConstraints(max_length=5000)]
long_str_type = Annotated[str, StringConstraints(max_length=10000)]


@strawberry.type
class BudgetType:
    """
    Class for info regarding a submitted budget

    Attributes:
        amount (float): Amount of the budget.
        description (str | None): Description of the budget. Defaults to None.
        advance (bool): Whether the budget is the required advance or not. 
                        Defaults to False.
    """

    amount: float
    description: str | None = None
    advance: bool = False

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, value):
        """
        A field validator for the amount field.
        """
        if value <= 0:
            raise ValueError("Amount must be positive")
        return value


@strawberry.enum
class PrizesType(StrEnum):
    """
    Enum for kind of prizes given to the participants in an event
    """
    win_certificates = auto()
    participation_certificates = auto()
    cash_prizes = auto()
    vouchers = auto()
    medals = auto()
    others = auto()


# for handling mongo ObjectIds
class PyObjectId(ObjectId):
    """
    Class for handling MongoDB document ObjectIds for 'id' fields in Models.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        return core_schema.union_schema(
            [
                # check if it's an instance first before doing any further work
                core_schema.is_instance_schema(ObjectId),
                core_schema.no_info_plain_validator_function(cls.validate),
            ],
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


# for storing a vaildating url's
http_url_adapter = TypeAdapter(HttpUrl)
HttpUrlString = Annotated[
    str,
    BeforeValidator(
        lambda value: str(http_url_adapter.validate_python(value))
    ),
]
# takes the time from IST timezone
timezone = pytz.timezone("Asia/Kolkata")
