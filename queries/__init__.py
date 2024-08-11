from queries.events import queries as events_queries
from queries.finances import queries as finances_queries
from queries.holidays import queries as holidays_queries

queries = [
    *events_queries,
    *finances_queries,
    *holidays_queries,
]