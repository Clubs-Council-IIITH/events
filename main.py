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

# check whether running in debug mode
DEBUG = int(getenv("GLOBAL_DEBUG", 0))

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

# serve API with FastAPI router
gql_app = GraphQLRouter(schema, graphiql=True, context_getter=get_context)
app = FastAPI(
    debug=DEBUG,
    title="CC Events Microservice",
    description="Handles Data of Events & Holidays",
)
app.include_router(gql_app, prefix="/graphql")
