import strawberry

from strawberry.tools import create_type
from strawberry.fastapi import GraphQLRouter

from fastapi import FastAPI

# import all queries and mutations
from queries import sampleQuery
from mutations import sampleMutation


# create query types
Query = create_type("Query", [sampleQuery])

# create mutation types
Mutation = create_type("Mutation", [sampleMutation])

# initialize federated schema
schema = strawberry.federation.Schema(
    query=Query,
    mutation=Mutation,
    enable_federation_2=True,
)

# serve API with FastAPI router
gql_app = GraphQLRouter(schema)
app = FastAPI()
app.include_router(gql_app, prefix="/graphql")
