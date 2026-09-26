"""Versioned dataset manifest and complete retained-evidence validation."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from arpg_build_lab.datasets.passive_point_allocations import (
    GENERATOR_VERSION,
    candidates,
)
from arpg_build_lab.domain.evaluation import canonical_bytes, sha256
from arpg_build_lab.domain.evaluation import load as load_evaluation
from arpg_build_lab.domain.snapshot import BuildSnapshot
from arpg_build_lab.evaluators.le_building import (
    APPLICATION_VERSION,
    EVALUATOR_VERSION,
    GAME_DATA,
    REVISION,
    supported,
)
from arpg_build_lab.importers.cli import load as load_import
from arpg_build_lab.importers.letools import validate_evaluation_source

SCHEMA_VERSION = 1
CONFIGURATION = {
    "nodes": {"49": {"minimum": 0, "maximum": 8}, "2": {"minimum": 0, "maximum": 5}},
    "order": "Fearless 49 ascending, then Armour Clad 2 ascending",
    "randomness": None,
}


@dataclass(frozen=True)
class Dataset:
    manifest: dict[str, Any]
    starting_snapshot: BuildSnapshot
    candidates: list[BuildSnapshot]


def snapshot_hash(snapshot: BuildSnapshot) -> str:
    return sha256(canonical_bytes(snapshot.to_dict()))


def _relative(value: Any, expected: str) -> Path:
    if value != expected:
        raise ValueError(f"Dataset path must be {expected}")
    return Path(expected)


def load(location: Path) -> Dataset:
    """Validate a complete dataset without consulting its original import run."""
    manifest = json.loads((location / "manifest.json").read_text())
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema_version",
        "snapshot_schema_version",
        "evaluation_schema_version",
        "game_version",
        "starting_snapshot",
        "generator",
        "evaluator",
        "candidate_count",
        "candidates",
        "measured_calculator_seconds",
    }:
        raise ValueError("Dataset manifest fields do not match schema 1")
    if (
        any(
            type(manifest[field]) is not int or manifest[field] != 1
            for field in (
                "schema_version",
                "snapshot_schema_version",
                "evaluation_schema_version",
            )
        )
        or manifest["game_version"] != "1.4.7"
    ):
        raise ValueError("Dataset schema or game version is unsupported")
    starting_snapshot_record = manifest["starting_snapshot"]
    if not isinstance(starting_snapshot_record, dict) or set(
        starting_snapshot_record
    ) != {
        "path",
        "snapshot_sha256",
        "source_url",
        "source_id",
        "raw_sha256",
        "provenance_sha256",
    }:
        raise ValueError("Dataset starting snapshot record is invalid")
    starting_snapshot_path = _relative(
        starting_snapshot_record["path"], "starting_snapshot"
    )
    starting_snapshot = load_import(location / starting_snapshot_path)
    validate_evaluation_source(
        (location / starting_snapshot_path / starting_snapshot.raw_path).read_bytes(),
        starting_snapshot,
    )
    supported(starting_snapshot)
    if starting_snapshot_record != {
        "path": "starting_snapshot",
        "snapshot_sha256": snapshot_hash(starting_snapshot),
        "source_url": starting_snapshot.source_url,
        "source_id": starting_snapshot.source_id,
        "raw_sha256": starting_snapshot.raw_sha256,
        "provenance_sha256": (
            sha256((location / starting_snapshot_path / "provenance.json").read_bytes())
            if (location / starting_snapshot_path / "provenance.json").is_file()
            else None
        ),
    }:
        raise ValueError(
            "Dataset starting snapshot identity does not match retained import"
        )
    if starting_snapshot.game_version != manifest["game_version"]:
        raise ValueError("Dataset starting snapshot game version differs from manifest")
    if manifest["generator"] != {
        "name": "sentinel_passive_space",
        "version": GENERATOR_VERSION,
        "configuration": CONFIGURATION,
    }:
        raise ValueError("Dataset generator configuration is unsupported")
    evaluator = manifest["evaluator"]
    if (
        not isinstance(evaluator, dict)
        or set(evaluator)
        != {
            "name",
            "version",
            "calculator_revision",
            "calculator_application_version",
            "calculator_game_data",
            "configuration",
        }
        or evaluator["name"] != "last_epoch_building"
        or evaluator["version"] != EVALUATOR_VERSION
        or evaluator["calculator_revision"] != REVISION
        or evaluator["calculator_application_version"] != APPLICATION_VERSION
        or evaluator["calculator_game_data"] != GAME_DATA
    ):
        raise ValueError("Dataset evaluator identity is unsupported")
    if not isinstance(evaluator["configuration"], dict):
        raise ValueError("Dataset evaluator configuration is invalid")
    if type(manifest["measured_calculator_seconds"]) not in (
        int,
        float,
    ) or not 0 <= manifest["measured_calculator_seconds"] < float("inf"):
        raise ValueError("Dataset measured calculator time is invalid")
    records = manifest["candidates"]
    expected = candidates(starting_snapshot)
    if (
        type(manifest["candidate_count"]) is not int
        or manifest["candidate_count"] != len(expected)
        or not isinstance(records, list)
        or len(records) != len(expected)
    ):
        raise ValueError("Dataset candidate count or coverage is incomplete")
    actual_dirs = {path.name for path in (location / "candidates").iterdir()}
    promised_dirs = {f"{index:03d}" for index in range(len(expected))}
    if actual_dirs != promised_dirs:
        raise ValueError("Dataset candidate directories differ from promised set")
    loaded = []
    for index, (record, wanted) in enumerate(zip(records, expected, strict=True)):
        if (
            not isinstance(record, dict)
            or set(record)
            != {"index", "snapshot_sha256", "evaluation_path", "evaluation_sha256"}
            or record["index"] != index
            or type(record["index"]) is not int
        ):
            raise ValueError(f"Candidate {index} record is invalid")
        candidate_path = _relative(record["evaluation_path"], f"candidates/{index:03d}")
        evaluation_path = location / candidate_path
        if not isinstance(record["evaluation_sha256"], str) or not re.fullmatch(
            r"[0-9a-f]{64}", record["evaluation_sha256"]
        ):
            raise ValueError(f"Candidate {index} evaluation hash is invalid")
        if (
            sha256((evaluation_path / "evaluation.json").read_bytes())
            != record["evaluation_sha256"]
        ):
            raise ValueError(f"Candidate {index} evaluation record hash differs")
        evaluation = load_evaluation(evaluation_path)
        snapshot = BuildSnapshot.from_dict(
            json.loads((evaluation_path / "snapshot.json").read_text())
        )
        expected_hash = snapshot_hash(wanted)
        if (
            record["snapshot_sha256"] != expected_hash
            or snapshot_hash(snapshot) != expected_hash
            or evaluation.snapshot_sha256 != expected_hash
        ):
            raise ValueError(
                f"Candidate {index} snapshot differs from promised passive point allocation"
            )
        if (
            evaluation.source_url,
            evaluation.source_id,
            evaluation.raw_sha256,
            evaluation.game_version,
        ) != (
            starting_snapshot.source_url,
            starting_snapshot.source_id,
            starting_snapshot.raw_sha256,
            starting_snapshot.game_version,
        ):
            raise ValueError(
                f"Candidate {index} source or game version differs from starting snapshot"
            )
        if {
            "name": evaluation.evaluator,
            "version": evaluation.evaluator_version,
            "calculator_revision": evaluation.calculator_revision,
            "calculator_application_version": evaluation.calculator_application_version,
            "calculator_game_data": evaluation.calculator_game_data,
            "configuration": evaluation.configuration,
        } != evaluator:
            raise ValueError(f"Candidate {index} evaluator configuration differs")
        loaded.append(snapshot)
    return Dataset(manifest, starting_snapshot, loaded)
