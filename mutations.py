import strawberry


@strawberry.mutation
def sampleMutation(info) -> str:
    return "Sample Mutation Result"
