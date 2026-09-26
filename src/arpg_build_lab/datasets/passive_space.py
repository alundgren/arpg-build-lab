"""Enumerate canonical passive mutations of one saved build."""

from arpg_build_lab.domain.passives import allocations
from arpg_build_lab.domain.snapshot import BuildSnapshot

GENERATOR_VERSION = "1"


def candidates(seed: BuildSnapshot) -> list[BuildSnapshot]:
    result = []
    for selected in allocations(seed.character["level"]):
        value = seed.to_dict()
        value["passives"]["selected"] = selected
        result.append(BuildSnapshot.from_dict(value))
    return result
