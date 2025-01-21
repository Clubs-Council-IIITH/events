"""
Gathers all the mutations form all the files within this folder and collects them for importing into main.py.
"""

from mutations.event_report import mutations as event_report_mutations
from mutations.events import mutations as events_mutations
from mutations.finances import mutations as finances_mutations
from mutations.holidays import mutations as holidays_mutations

mutations = [
    *events_mutations,
    *event_report_mutations,
    *finances_mutations,
    *holidays_mutations,
]