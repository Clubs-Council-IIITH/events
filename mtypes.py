import strawberry
from bson import ObjectId
from enum import StrEnum, auto
from pydantic import Field, StringConstraints, field_validator
from pydantic_core import core_schema
from typing_extensions import Annotated, Any


# Audience of Events
@strawberry.enum
class Audience(StrEnum):
    ug1 = auto()
    ug2 = auto()
    ug3 = auto()
    ug4 = auto()
    pg = auto()
    stf = auto()
    fac = auto()
    internal = auto()


# Event States
@strawberry.enum
class Event_State_Status(StrEnum):
    # initially, the event is `incomplete`
    incomplete = auto()
    # after the club fills all the details, they progress it
    pending_cc = auto()
    # cc chooses to progress the state status, the budget status and the room status
    # if budget status is unapproved, the event is `pending_budget`, else skip to next
    pending_budget = auto()
    # after budget is approved (through any track),
    # if room status is unapproved, the event is `pending_room`, else skip to next
    pending_room = auto()
    # after room is approved (through any track), the event is `approved`
    approved = auto()
    # if the event is deleted, its state is `deleted`
    deleted = auto()


# @strawberry.enum
# class Event_Room_Status (Enum) :
#     unapproved = auto()
#     approved = auto()
# @strawberry.enum
# class Event_Budget_Status (Enum) :
#     unapproved = auto()
#     approved = auto()


@strawberry.type
class Event_Status:
    state: Event_State_Status = Event_State_Status.incomplete
    # room: Event_Room_Status = Event_Room_Status.unapproved
    # budget: Event_Budget_Status = Event_Budget_Status.unapproved
    room: bool = False
    budget: bool = False
    cc_approver: str | None = None
    slo_approver: str | None = None
    slc_approver: str | None = None

    # def __init__ (self, state: Event_State_Status = None, room: Event_Room_Status = None, budget: Event_Budget_Status = None) :
    #     self.state: Event_State_Status = Event_State_Status.incomplete if state is None else state
    #     self.room: Event_Room_Status = Event_Room_Status.unapproved if room is None else room
    #     self.budget: Event_Budget_Status = Event_Budget_Status.unapproved if budget is None else budget
    def __init__(
        self,
        state: Event_State_Status = Event_State_Status.incomplete,
        room: bool = False,
        budget: bool = False,
        cc_approver: str | None = None,
        slo_approver: str | None = None,
        slc_approver: str | None = None,
    ):
        self.state = state
        self.room = room
        self.budget = budget
        self.cc_approver = cc_approver
        self.slo_approver = slo_approver
        self.slc_approver = slc_approver


# Event Modes
@strawberry.enum
class Event_Mode(StrEnum):
    hybrid = auto()
    online = auto()
    offline = auto()


# Event Full Locations
class Event_Full_Location:
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


event_name_type = Annotated[str, StringConstraints(min_length=1, max_length=200)]
event_desc_type = Annotated[str, StringConstraints(max_length=5000)]
event_popu_type = Annotated[int, Field(ge=0)]
event_othr_type = Annotated[str, StringConstraints(max_length=1000)]


@strawberry.type
class BudgetType:
    amount: float
    description: str | None = None
    advance: bool = False

    # Validators
    @field_validator("amount")
    @classmethod
    def positive_amount(cls, value):
        if value <= 0:
            raise ValueError("Amount must be positive")
        return value


# for handling mongo ObjectIds
class PyObjectId(ObjectId):
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
