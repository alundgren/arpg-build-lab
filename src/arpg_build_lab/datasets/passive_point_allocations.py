"""Enumerate canonical passive point allocations from one starting snapshot."""

from arpg_build_lab.domain.passives import allocations
from arpg_build_lab.domain.snapshot import BuildSnapshot

GENERATOR_VERSION = "1"


def candidates(starting_snapshot: BuildSnapshot) -> list[BuildSnapshot]:
    result = []
    for selected in allocations(starting_snapshot.character["level"]):
        value = starting_snapshot.to_dict()
        value["passives"]["selected"] = selected
        result.append(BuildSnapshot.from_dict(value))
    return result
