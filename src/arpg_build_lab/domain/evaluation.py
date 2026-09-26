"""Versioned reference evaluation and retained-file integrity contract."""

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from arpg_build_lab.domain.snapshot import BuildSnapshot


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class BuildEvaluation:
    schema_version: int
    snapshot_schema_version: int
    game_version: str
    source_url: str
    source_id: str
    raw_sha256: str
    snapshot_sha256: str
    evaluator: str
    evaluator_version: str
    calculator_revision: str
    calculator_application_version: str
    calculator_game_data: str
    runtime: str
    runtime_version: str
    configuration: dict[str, Any]
    metrics: dict[str, dict[str, Any]]
    files: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Any) -> "BuildEvaluation":
        if not isinstance(value, dict) or set(value) != set(cls.__dataclass_fields__):
            raise ValueError("Evaluation fields do not match schema 1")
        if type(value["schema_version"]) is not int or value["schema_version"] != 1:
            raise ValueError("Unsupported evaluation schema version")
        if (
            type(value["snapshot_schema_version"]) is not int
            or value["snapshot_schema_version"] != 1
        ):
            raise ValueError("Unsupported snapshot schema version")
        for key in (
            "game_version",
            "source_url",
            "source_id",
            "evaluator",
            "evaluator_version",
            "calculator_revision",
            "calculator_application_version",
            "calculator_game_data",
            "runtime",
            "runtime_version",
        ):
            if not isinstance(value[key], str) or not value[key]:
                raise ValueError(f"Evaluation {key} must be a nonempty string")
        for key in ("raw_sha256", "snapshot_sha256"):
            if not isinstance(value[key], str) or not re.fullmatch(
                r"[0-9a-f]{64}", value[key]
            ):
                raise ValueError(f"Evaluation {key} must be SHA-256")
        if not isinstance(value["configuration"], dict):
            raise ValueError("Evaluation configuration must be an object")
        if not isinstance(value["metrics"], dict) or set(value["metrics"]) != {
            "health",
            "armour",
        }:
            raise ValueError("Evaluation requires health and armour")
        for name, unit in (("health", "health points"), ("armour", "armour rating")):
            metric = value["metrics"][name]
            if (
                not isinstance(metric, dict)
                or set(metric) != {"value", "unit"}
                or metric["unit"] != unit
            ):
                raise ValueError(f"Invalid {name} unit")
            number = metric["value"]
            try:
                valid = (
                    type(number) in (int, float)
                    and math.isfinite(number)
                    and number >= 0
                )
            except OverflowError:
                valid = False
            if not valid:
                raise ValueError(f"Invalid {name} value")
        if not isinstance(value["files"], dict) or set(value["files"]) != {
            "snapshot.json",
            "calculator-input.xml",
            "calculator-output.json",
            "diagnostics.json",
        }:
            raise ValueError("Evaluation file links are incomplete")
        for name, digest in value["files"].items():
            if (
                Path(name).name != name
                or not isinstance(digest, str)
                or not re.fullmatch(r"[0-9a-f]{64}", digest)
            ):
                raise ValueError(f"Invalid evaluation file link: {name}")
        try:
            canonical_bytes(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Evaluation contains invalid JSON") from exc
        return cls(**value)


def load(location: Path) -> BuildEvaluation:
    value = json.loads(
        (location / "evaluation.json").read_text(),
        parse_constant=lambda x: (_ for _ in ()).throw(
            ValueError(f"Invalid number: {x}")
        ),
    )
    evaluation = BuildEvaluation.from_dict(value)
    for name, digest in evaluation.files.items():
        if sha256((location / name).read_bytes()) != digest:
            raise ValueError(f"Evaluation file hash mismatch: {name}")
    snapshot = BuildSnapshot.from_dict(
        json.loads((location / "snapshot.json").read_text())
    )
    if sha256(canonical_bytes(snapshot.to_dict())) != evaluation.snapshot_sha256:
        raise ValueError("Evaluated snapshot content hash mismatch")
    if (
        snapshot.schema_version,
        snapshot.game_version,
        snapshot.source_url,
        snapshot.source_id,
        snapshot.raw_sha256,
    ) != (
        evaluation.snapshot_schema_version,
        evaluation.game_version,
        evaluation.source_url,
        evaluation.source_id,
        evaluation.raw_sha256,
    ):
        raise ValueError("Evaluation source identity does not match snapshot")
    return evaluation
