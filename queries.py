import strawberry

from otypes import SampleType


# sample query
@strawberry.field
def sampleQuery(info) -> SampleType:
    return SampleType(id=0, attribute="sample")
