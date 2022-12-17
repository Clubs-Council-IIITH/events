import strawberry

from otypes import SampleInput, SampleType


# sample mutation
@strawberry.mutation
def sampleMutation(sampleInput: SampleInput) -> SampleType:
    return SampleType(id=-1, attribute=sampleInput.attribute)
