import strawberry

from strawberry.tools import create_type
from strawberry.fastapi import GraphQLRouter

from fastapi import FastAPI

# override PyObjectId and Context scalars
from models import PyObjectId
from otypes import Context, PyObjectIdType

# import all queries and mutations
from queries import queries
from mutations import mutations


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
gql_app = GraphQLRouter(schema, context_getter=get_context)
app = FastAPI()
app.include_router(gql_app, prefix="/graphql")
