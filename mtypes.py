import strawberry
from bson import ObjectId

from enum import (
    Enum,
    auto,
)
from pydantic import (
    constr,
    conint,
)

# Audience of Events
@strawberry.enum
class Audience (Enum) :
    ug1 = auto()
    ug2 = auto()
    ug3 = auto()
    ug4 = auto()
    pg  = auto()
    stf = auto()
    fac = auto()

audience_mapping = {
    Audience.ug1  : 'UG 1',
    Audience.ug2  : 'UG 2',
    Audience.ug3  : 'UG 3',
    Audience.ug4  : 'UG 4+',
    Audience.pg   : 'PG',
    Audience.stf  : 'Staff',
    Audience.fac  : 'Faculty',
}

# Event States
@strawberry.enum
class Event_State_Status (Enum) :
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
    completed  = auto()
    # if the event is deleted, its state is `deleted`
    deleted = auto()
@strawberry.enum
class Event_Room_Status (Enum) :
    unapproved = auto()
    approved = auto()
@strawberry.enum
class Event_Budget_Status (Enum) :
    unapproved = auto()
    approved = auto()

@strawberry.type
class Event_Status :
    state: Event_State_Status = Event_State_Status.incomplete
    room: Event_Room_Status = Event_Room_Status.unapproved
    budget: Event_Budget_Status = Event_Budget_Status.unapproved

    def __init__ (self, state: Event_State_Status = None, room: Event_Room_Status = None, budget: Event_Budget_Status = None) :
        self.state: Event_State_Status = Event_State_Status.incomplete if state is None else state
        self.room: Event_Room_Status = Event_Room_Status.unapproved if room is None else room
        self.budget: Event_Budget_Status = Event_Budget_Status.unapproved if budget is None else budget

# Event Modes
@strawberry.enum
class Event_Mode (Enum) :
    hybrid  = auto()
    online  = auto()
    offline = auto()

# Event Locations
@strawberry.enum
class Event_Location (Enum) :
    # Himalaya
    H101 = auto()
    H102 = auto()
    H103 = auto()
    H104 = auto()
    H201 = auto()
    H202 = auto()
    H203 = auto()
    H204 = auto()
    H301 = auto()
    H302 = auto()
    H303 = auto()
    H304 = auto()
    # Vindhya
    VA3_117 = auto()
    VSH1 = auto()
    VSH2 = auto()
    # Other
    AMPI = auto()
    CIEg = auto()
    SARG = auto()
    # Academic Rooms
    H105 = auto()
    H205 = auto()
    # KRB
    KRBa = auto()
    LM22 = auto()
    SM24 = auto()
    SM32 = auto()
    LM34 = auto()
    # nota
    other = auto()

location_mapping = {
    Event_Location.H101    : 'Himalaya 101',
    Event_Location.H102    : 'Himalaya 102',
    Event_Location.H103    : 'Himalaya 103',
    Event_Location.H104    : 'Himalaya 104',
    Event_Location.H201    : 'Himalaya 201',
    Event_Location.H202    : 'Himalaya 202',
    Event_Location.H203    : 'Himalaya 203',
    Event_Location.H204    : 'Himalaya 204',
    Event_Location.H301    : 'Himalaya 301',
    Event_Location.H302    : 'Himalaya 302',
    Event_Location.H303    : 'Himalaya 303',
    Event_Location.H304    : 'Himalaya 304',
    Event_Location.VA3_117 : 'Vindhya A3 117',
    Event_Location.VSH1    : 'Vindhya SH1',
    Event_Location.VSH2    : 'Vindhya SH2',
    Event_Location.AMPI    : 'Amphitheatre',
    Event_Location.CIEg    : 'CIE Gaming',
    Event_Location.SARG    : 'Saranga Hall',
    Event_Location.H105    : 'Himalaya 105',
    Event_Location.H205    : 'Himalaya 205',
    Event_Location.KRBa    : 'KRB Auditorium',
    Event_Location.LM22    : 'LM-22, KRB',
    Event_Location.SM24    : 'SM-24, KRB',
    Event_Location.SM32    : 'SM-32, KRB',
    Event_Location.LM34    : 'LM-34, KRB',
    Event_Location.other   : 'Other',
}

event_name_type = constr(min_length=1, max_length=20)
event_desc_type = constr(max_length=5000)
event_popu_type = conint(ge=0)
event_othr_type = constr(max_length=1000)

class BudgetType :
    amount: float
    description: event_desc_type | None = None
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