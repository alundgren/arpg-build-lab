"""Persisted build snapshot contract. IDs retain their declared namespace."""

import json
import math
import re
from dataclasses import asdict, dataclass
from typing import Any, TypedDict

SCHEMA_VERSION = 1


class Character(TypedDict):
    class_id: int | None
    mastery_id: int | None
    level: int | None
    source_fields: dict[str, Any]


class Tree(TypedDict):
    source_tree_id: str | None
    source_namespace: str
    selected: dict[str, int]
    level: int | None
    slot_number: int | None
    source_version: int | None


class Translation(TypedDict):
    base_type_id: int | None
    sub_type_id: int | None
    unique_id: int | None
    lookup_extra: dict[str, Any]


class Affix(TypedDict):
    source_id: str
    source_namespace: str
    translated_id: int | None
    tier: int | None
    roll: int | float | None
    source_fields: dict[str, Any]


class Item(TypedDict):
    source_id: str
    source_namespace: str
    translation: Translation | None
    affixes: list[Affix]
    special_affixes: dict[str, Affix]
    source_fields: dict[str, Any]


class Idol(Item):
    x: int | None
    y: int | None


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(k, str) for k in value):
        raise ValueError(f"{path} must be an object with string keys")
    return value


def _array(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{path} must be a list")
    return value


def _string(value: Any, path: str, optional: bool = False) -> None:
    if (value is None and optional) or isinstance(value, str):
        return
    raise ValueError(f"{path} must be a string{' or null' if optional else ''}")


def _integer(value: Any, path: str, optional: bool = False) -> None:
    if (value is None and optional) or (type(value) is int):
        return
    raise ValueError(f"{path} must be an integer{' or null' if optional else ''}")


def _number(value: Any, path: str, optional: bool = False) -> None:
    if value is None and optional:
        return
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{path} must be a finite number{' or null' if optional else ''}")


def _fields(value: dict[str, Any], names: set[str], path: str) -> None:
    if set(value) != names:
        raise ValueError(f"{path} must have fields {', '.join(sorted(names))}")


def _tree(value: Any, path: str) -> None:
    obj = _object(value, path)
    _fields(obj, {"source_tree_id", "source_namespace", "selected", "level", "slot_number", "source_version"}, path)
    _string(obj["source_tree_id"], f"{path}.source_tree_id", True)
    _string(obj["source_namespace"], f"{path}.source_namespace")
    for node, points in _object(obj["selected"], f"{path}.selected").items():
        _integer(points, f"{path}.selected.{node}")
    for key in ("level", "slot_number", "source_version"):
        _integer(obj[key], f"{path}.{key}", True)


def _affix(value: Any, path: str) -> None:
    obj = _object(value, path)
    _fields(obj, {"source_id", "source_namespace", "translated_id", "tier", "roll", "source_fields"}, path)
    _string(obj["source_id"], f"{path}.source_id")
    _string(obj["source_namespace"], f"{path}.source_namespace")
    _integer(obj["translated_id"], f"{path}.translated_id", True)
    _integer(obj["tier"], f"{path}.tier", True)
    _number(obj["roll"], f"{path}.roll", True)
    _object(obj["source_fields"], f"{path}.source_fields")


def _item(value: Any, path: str, idol: bool = False) -> None:
    obj = _object(value, path)
    names = {"source_id", "source_namespace", "translation", "affixes", "special_affixes", "source_fields"}
    if idol:
        names |= {"x", "y"}
    _fields(obj, names, path)
    _string(obj["source_id"], f"{path}.source_id")
    _string(obj["source_namespace"], f"{path}.source_namespace")
    if obj["translation"] is not None:
        translation = _object(obj["translation"], f"{path}.translation")
        _fields(translation, {"base_type_id", "sub_type_id", "unique_id", "lookup_extra"}, f"{path}.translation")
        for key in ("base_type_id", "sub_type_id", "unique_id"):
            _integer(translation[key], f"{path}.translation.{key}", True)
        _object(translation["lookup_extra"], f"{path}.translation.lookup_extra")
    for i, affix in enumerate(_array(obj["affixes"], f"{path}.affixes")):
        _affix(affix, f"{path}.affixes[{i}]")
    for name, affix in _object(obj["special_affixes"], f"{path}.special_affixes").items():
        _affix(affix, f"{path}.special_affixes.{name}")
    _object(obj["source_fields"], f"{path}.source_fields")
    if idol:
        for key in ("x", "y"):
            _integer(obj[key], f"{path}.{key}", True)


@dataclass(frozen=True)
class BuildSnapshot:
    schema_version: int
    game_version: str | None
    version_evidence: dict[str, str | None]
    importer_version: str
    lookup_revision: str
    source_url: str
    source_id: str
    raw_path: str
    raw_sha256: str
    character: Character
    passives: Tree
    skills: list[Tree]
    equipment: dict[str, Item]
    idols: list[Idol]
    blessings: dict[str, Item]
    unresolved: dict[str, list[str]]
    unsupported_sections: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "BuildSnapshot":
        obj = _object(value, "snapshot")
        _fields(obj, set(cls.__dataclass_fields__), "snapshot")
        if obj["schema_version"] != SCHEMA_VERSION or type(obj["schema_version"]) is not int:
            raise ValueError(f"Unsupported snapshot schema version: {obj['schema_version']!r}")
        _string(obj["game_version"], "game_version", True)
        versions = _object(obj["version_evidence"], "version_evidence")
        for key, evidence in versions.items():
            _string(evidence, f"version_evidence.{key}", True)
        for key in ("importer_version", "lookup_revision", "source_url", "source_id", "raw_path", "raw_sha256"):
            _string(obj[key], key)
        if not re.fullmatch(r"[0-9a-f]{64}", obj["raw_sha256"]):
            raise ValueError("raw_sha256 must be a lowercase SHA-256 hex digest")
        character = _object(obj["character"], "character")
        _fields(character, {"class_id", "mastery_id", "level", "source_fields"}, "character")
        for key in ("class_id", "mastery_id", "level"):
            _integer(character[key], f"character.{key}", True)
        _object(character["source_fields"], "character.source_fields")
        _tree(obj["passives"], "passives")
        for i, tree in enumerate(_array(obj["skills"], "skills")):
            _tree(tree, f"skills[{i}]")
        for slot, item in _object(obj["equipment"], "equipment").items():
            _item(item, f"equipment.{slot}")
        for i, item in enumerate(_array(obj["idols"], "idols")):
            _item(item, f"idols[{i}]", idol=True)
        for slot, item in _object(obj["blessings"], "blessings").items():
            _item(item, f"blessings.{slot}")
        diagnostics = _object(obj["unresolved"], "unresolved")
        _fields(diagnostics, {"item_ids", "affix_ids", "blessing_ids"}, "unresolved")
        for kind, values in diagnostics.items():
            for i, item_id in enumerate(_array(values, f"unresolved.{kind}")):
                _string(item_id, f"unresolved.{kind}[{i}]")
        for i, section in enumerate(_array(obj["unsupported_sections"], "unsupported_sections")):
            _string(section, f"unsupported_sections[{i}]")
        try:
            json.dumps(obj, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Snapshot contains invalid JSON data: {exc}") from exc
        return cls(**obj)
