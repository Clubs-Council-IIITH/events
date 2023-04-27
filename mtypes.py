import strawberry
from bson import ObjectId
from enum import StrEnum, auto
from pydantic import constr, conint


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
    # once the finishing time of the event passes, the state moves to `completed`
    completed = auto()
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

    # def __init__ (self, state: Event_State_Status = None, room: Event_Room_Status = None, budget: Event_Budget_Status = None) :
    #     self.state: Event_State_Status = Event_State_Status.incomplete if state is None else state
    #     self.room: Event_Room_Status = Event_Room_Status.unapproved if room is None else room
    #     self.budget: Event_Budget_Status = Event_Budget_Status.unapproved if budget is None else budget
    def __init__(
        self,
        state: Event_State_Status = Event_State_Status.incomplete,
        room: bool = False,
        budget: bool = False,
    ):
        self.state = state
        self.room = room
        self.budget = budget


# Event Modes
@strawberry.enum
class Event_Mode(StrEnum):
    hybrid = auto()
    online = auto()
    offline = auto()


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
    ampi = auto()
    cieg = auto()
    sarg = auto()
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


event_name_type = constr(min_length=1, max_length=100)
event_desc_type = constr(max_length=5000)
event_popu_type = conint(ge=0)
event_othr_type = constr(max_length=1000)


@strawberry.type
class BudgetType:
    amount: float
    description: str | None = None
    reimbursable: bool = False


# for handling mongo ObjectIds
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")
