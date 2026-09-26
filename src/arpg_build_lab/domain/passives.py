"""Supported Sentinel passive allocations for the current calculator subset."""


def validate(selected: dict[str, int], level: int) -> dict[str, int]:
    unsupported = sorted(set(selected) - {"49", "2"})
    if unsupported:
        raise ValueError(
            f"passives.selected.{unsupported[0]} is unsupported; only Fearless 49 and Armour Clad 2 are supported"
        )
    for key, maximum in (("49", 8), ("2", 5)):
        points = selected.get(key, 0)
        if type(points) is not int or not 0 <= points <= maximum:
            raise ValueError(
                f"passives.selected.{key} must be an integer from 0 to {maximum}"
            )
    if selected.get("2", 0) and selected.get("49", 0) < 5:
        raise ValueError("Armour Clad 2 requires at least five Fearless 49 points")
    if sum(selected.values()) > level - 1:
        raise ValueError(
            "passives.selected exceeds the conservative level - 1 point budget"
        )
    return {key: count for key, count in selected.items() if count}


def allocations(level: int) -> list[dict[str, int]]:
    """Order valid allocations by Fearless points, then Armour Clad points."""
    result = []
    for fearless in range(9):
        for armour_clad in range(6):
            selected = {
                key: count
                for key, count in (("49", fearless), ("2", armour_clad))
                if count
            }
            try:
                validate(selected, level)
            except ValueError:
                continue
            result.append(selected)
    return result
