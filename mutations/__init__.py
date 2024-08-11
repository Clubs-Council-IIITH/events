from mutations.events import mutations as events_mutations
from mutations.finances import mutations as finances_mutations
from mutations.holidays import mutations as holidays_mutations

mutations = [
    *events_mutations,
    *finances_mutations,
    *holidays_mutations,
]