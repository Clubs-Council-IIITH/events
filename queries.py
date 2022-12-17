import strawberry


@strawberry.field
def sampleQuery(info) -> str:
    return "Sample Query Result"
