"""
Main module for the Events Microservice.

This module sets up the FastAPI application and integrates the Strawberry GraphQL schema.
It includes the configuration for queries, mutations, and context.

Attributes:
    GLOBAL_DEBUG (str): Environment variable that Enables or Disables debug mode. Defaults to "False".
    DEBUG (bool): Indicates whether the application is running in debug mode.
    gql_app (GraphQLRouter): The GraphQL router for handling GraphQL requests.
    app (FastAPI): The FastAPI application instance.
"""

from os import getenv

import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from strawberry.tools import create_type

# import queries, mutations, PyObjectId and Context scalars
from mtypes import PyObjectId
from mutations import mutations
from otypes import Context, PyObjectIdType
from queries import queries

# create query types
Query = create_type("Query", queries)

# create mutation types
Mutation = create_type("Mutation", mutations)


# override context getter
async def get_context() -> Context:
    return Context()


# initialize federated schema
schema = strawberry.federation.Schema(
    query=Query,
    mutation=Mutation,
    enable_federation_2=True,
    scalar_overrides={PyObjectId: PyObjectIdType},
)

# check whether running in debug mode
DEBUG = getenv("GLOBAL_DEBUG", "False").lower() in ("true", "1", "t")

# serve API with FastAPI router
gql_app = GraphQLRouter(schema, graphiql=True, context_getter=get_context)
app = FastAPI(
    debug=DEBUG,
    title="CC Events Microservice",
    description="Handles Data of Events & Holidays",
)
app.include_router(gql_app, prefix="/graphql")
