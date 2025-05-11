"""
Gathers all the queries form all the files within this folder and collects them for importing into main.py.
""" # noqa: E501
from queries.event_report import queries as event_report_queries
from queries.events import queries as events_queries
from queries.finances import queries as finances_queries
from queries.holidays import queries as holidays_queries

queries = [
    *events_queries,
    *event_report_queries,
    *finances_queries,
    *holidays_queries,
]
