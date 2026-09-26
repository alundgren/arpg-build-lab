"""Import one explicitly requested LETools planner response."""

import hashlib
import json
import re
import urllib.error
import urllib.request
from importlib.resources import files
from typing import Any
from urllib.parse import urlsplit

from arpg_build_lab.domain.snapshot import BuildSnapshot, SCHEMA_VERSION

IMPORTER_VERSION = "1"
LOOKUP_REVISION = "uta666XYZ/LastEpochBuilding@a97d388aca0da00907afb9d5a945c8f254a67b18"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
PLANNER_ID = re.compile(r"[A-Za-z0-9]{8,64}\Z")
VERSION = re.compile(r"(?:Version\s+)?(\d+\.\d+\.\d+(?:[.-][A-Za-z0-9]+)?)\Z")
KNOWN_SECTIONS = {"fromSaveFile", "newGrid", "bio", "equipment", "idols", "blessings", "charTree", "skillTrees", "dataVersion"}
KNOWN_TOP = {"data", "created_for_build", "data_version"}


class ImportError(ValueError):
    """A requested build could not be imported."""


def planner_id(url: str) -> str:
    parts = urlsplit(url)
    path = parts.path.split("/")
    if (parts.scheme != "https" or parts.netloc != "www.lastepochtools.com"
            or parts.query or parts.fragment or len(path) != 3
            or path[:2] != ["", "planner"] or not PLANNER_ID.fullmatch(path[2])):
        raise ImportError("Expected https://www.lastepochtools.com/planner/<id> with no query or fragment")
    return path[2]


def fetch(url: str, timeout: float = 20) -> bytes:
    identifier = planner_id(url)
    request = urllib.request.Request(
        f"https://www.lastepochtools.com/api/public/build_data/{identifier}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        opener = urllib.request.build_opener(_NoRedirect)
        with opener.open(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise ImportError(f"LETools returned HTTP {exc.code} for planner {identifier}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ImportError(f"Could not fetch planner {identifier}: {exc.reason if isinstance(exc, urllib.error.URLError) else 'timed out'}") from exc


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request: Any, fp: Any, code: int, msg: str,
                         headers: Any, newurl: str) -> None:
        return None


def _mapping(name: str) -> dict[str, Any]:
    return json.loads(files("arpg_build_lab.importers").joinpath("data", name).read_text())


def _record(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ImportError(f"Expected {name} to be an object")
    return value


def _list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ImportError(f"Expected {name} to be a list")
    return value


def _version(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    match = VERSION.fullmatch(value.strip())
    return match.group(1) if match else None


def _json_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON number: {value}")


def _evidence(value: dict[str, Any], key: str, path: str) -> str | None:
    field = value.get(key)
    if field is not None and not isinstance(field, str):
        raise ImportError(f"Expected {path} to be a string or null")
    return field


def parse_build(raw: bytes, source_url: str) -> BuildSnapshot:
    identifier = planner_id(source_url)
    try:
        payload = json.loads(raw, parse_constant=_json_constant)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ImportError("LETools response is not valid JSON") from exc
    top = _record(payload, "response")
    data = _record(top.get("data"), "data")
    bio = _record(data.get("bio"), "data.bio")
    if not any(k in bio for k in ("level", "characterClass", "chosenMastery")):
        raise ImportError("data.bio has no character identity")
    versions = {key: _evidence(top, key, key) for key in ("created_for_build", "data_version")}
    versions["data.dataVersion"] = _evidence(data, "dataVersion", "data.dataVersion")
    parsed = [_version(v) for v in versions.values()]
    game_version = parsed[0] if all(v is not None and v == parsed[0] for v in parsed) else None

    item_map = _mapping("letools_item_map.json")
    affix_map = _mapping("letools_affix_map.json")
    unknown_items: set[str] = set()
    unknown_affixes: set[str] = set()
    unknown_blessings: set[str] = set()

    def affix(value: Any, name: str) -> dict[str, Any]:
        source = _record(value, name)
        source_id = source.get("id")
        if not isinstance(source_id, str):
            raise ImportError(f"Expected {name}.id to be a string")
        translated = affix_map.get(source_id)
        if translated is None:
            unknown_affixes.add(source_id)
        return {"source_id": source_id, "source_namespace": "letools.affix", "translated_id": translated,
                "tier": source.get("tier"), "roll": source.get("r"), "source_fields": source}

    def item(value: Any, name: str, *, namespace: str = "letools.item") -> dict[str, Any]:
        source = _record(value, name)
        source_id = source.get("id")
        if not isinstance(source_id, str):
            raise ImportError(f"Expected {name}.id to be a string")
        translated = item_map.get(source_id)
        if translated is None:
            (unknown_blessings if namespace == "letools.blessing" else unknown_items).add(source_id)
        for key in ("ir", "ur"):
            if key in source and source[key] is not None and (type(source[key]) not in (int, float)):
                raise ImportError(f"Expected {name}.{key} to be a number or null")
        regular = _list(source.get("affixes", []), f"{name}.affixes")
        translation = None if translated is None else {
            "base_type_id": translated.get("b"), "sub_type_id": translated.get("s"),
            "unique_id": translated.get("u"),
            "lookup_extra": {key: value for key, value in translated.items() if key not in ("b", "s", "u")},
        }
        return {"source_id": source_id, "source_namespace": namespace, "translation": translation,
                "affixes": [affix(a, f"{name}.affixes[{i}]") for i, a in enumerate(regular)],
                "special_affixes": {slot: affix(source[slot], f"{name}.{slot}") for slot in
                                    ("sealedAffix", "primordialAffix", "corruptedAffix") if slot in source and source[slot] is not None},
                "source_fields": source}

    def tree(value: Any, name: str) -> dict[str, Any]:
        source = _record(value, name)
        selected = _record(source.get("selected"), f"{name}.selected")
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in selected.values()):
            raise ImportError(f"Expected integer allocation counts in {name}.selected")
        return {"source_tree_id": source.get("treeID"), "source_namespace": "letools.tree",
                "selected": selected, "level": source.get("level"), "slot_number": source.get("slotNumber"),
                "source_version": source.get("version")}

    equipment = _record(data.get("equipment"), "data.equipment")
    idols = _list(data.get("idols"), "data.idols")
    blessings = _record(data.get("blessings"), "data.blessings")
    skills = _list(data.get("skillTrees"), "data.skillTrees")
    snapshot = BuildSnapshot(
        schema_version=SCHEMA_VERSION, game_version=game_version, version_evidence=versions,
        importer_version=IMPORTER_VERSION, lookup_revision=LOOKUP_REVISION,
        source_url=source_url, source_id=identifier, raw_path="raw.json",
        raw_sha256=hashlib.sha256(raw).hexdigest(),
        character={"class_id": bio.get("characterClass"), "mastery_id": bio.get("chosenMastery"),
                   "level": bio.get("level"), "source_fields": bio},
        passives=tree(data.get("charTree"), "data.charTree"),
        skills=[tree(s, f"data.skillTrees[{i}]") for i, s in enumerate(skills)],
        equipment={slot: item(value, f"data.equipment.{slot}") for slot, value in equipment.items()},
        idols=[{"x": _record(v, f"data.idols[{i}]").get("x"), "y": v.get("y"),
                **item(v, f"data.idols[{i}]")} for i, v in enumerate(idols)],
        blessings={key: item(value, f"data.blessings.{key}", namespace="letools.blessing")
                   for key, value in blessings.items()},
        unresolved={"item_ids": sorted(unknown_items), "affix_ids": sorted(unknown_affixes),
                    "blessing_ids": sorted(unknown_blessings)},
        unsupported_sections=sorted([f"data.{key}" for key in set(data) - KNOWN_SECTIONS]
                                    + [f"response.{key}" for key in set(top) - KNOWN_TOP]),
    )
    try:
        return BuildSnapshot.from_dict(snapshot.to_dict())
    except ValueError as exc:
        raise ImportError(f"Invalid LETools response: {exc}") from exc
