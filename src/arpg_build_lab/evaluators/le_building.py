"""Evaluate a narrow Sentinel subset with a pinned Last Epoch Building checkout."""

import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from arpg_build_lab.domain.evaluation import (
    BuildEvaluation,
    canonical_bytes,
    load,
    sha256,
)
from arpg_build_lab.domain.snapshot import BuildSnapshot

REVISION = "a97d388aca0da00907afb9d5a945c8f254a67b18"
APPLICATION_VERSION = "0.14.0"
EVALUATOR_VERSION = "1"
GAME_DATA = "1_4"
CONFIG_DEFAULTS = {
    "falconAvianArsenalPool": 0,
    "leBossCategory": "Empowered Monolith Boss",
    "minionMultiSkillCadenceFold": True,
    "repeatMode": "AVERAGE",
    "resourceGainMode": "AVERAGE",
}


def supported(snapshot: BuildSnapshot) -> dict[str, int]:
    if snapshot.game_version != "1.4.7" or set(snapshot.version_evidence) != {
        "created_for_build",
        "data_version",
        "data.dataVersion",
    }:
        raise ValueError("game_version and version_evidence must establish 1.4.7")
    if any(
        value not in ("Version 1.4.7", "1.4.7")
        for value in snapshot.version_evidence.values()
    ):
        raise ValueError("version_evidence must identify 1.4.7 in every source field")
    character = snapshot.character
    if character["class_id"] != 2 or type(character["class_id"]) is not int:
        raise ValueError("character.class_id supports only Sentinel ID 2")
    if character["mastery_id"] != 0 or type(character["mastery_id"]) is not int:
        raise ValueError("character.mastery_id supports only no mastery (0)")
    level = character["level"]
    if type(level) is not int or not 1 <= level <= 100:
        raise ValueError("character.level must be an integer from 1 to 100")
    source_fields = character["source_fields"]
    if any(
        type(source_fields.get(key)) is not int
        for key in ("characterClass", "chosenMastery", "level")
    ) or source_fields != {
        "characterClass": 2,
        "chosenMastery": 0,
        "level": level,
    }:
        raise ValueError(
            "character.source_fields supports only class, mastery, and level"
        )
    tree = snapshot.passives
    if (
        tree["source_namespace"] != "letools.tree"
        or tree["source_tree_id"] != ""
        or tree["level"] is not None
        or tree["slot_number"] is not None
        or tree["source_version"] != 1
    ):
        raise ValueError(
            "passives supports only the LETools Sentinel class tree without extra fields"
        )
    selected = tree["selected"]
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
    for name in ("skills", "equipment", "idols", "blessings", "unsupported_sections"):
        if getattr(snapshot, name):
            detail = (
                f" ({snapshot.unsupported_sections[0]})"
                if name == "unsupported_sections"
                else ""
            )
            raise ValueError(f"{name}{detail} must be empty for supported evaluation")
    if any(snapshot.unresolved.values()):
        raise ValueError("unresolved IDs must be empty for supported evaluation")
    return {key: count for key, count in selected.items() if count}


def calculator_xml(level: int, selected: dict[str, int]) -> str:
    root = ET.Element("LastEpochBuilding")
    ET.SubElement(
        root,
        "Build",
        level=str(level),
        targetVersion=GAME_DATA,
        className="Sentinel",
        ascendClassName="None",
        mainSocketGroup="1",
        viewMode="TREE",
        characterLevelAutoMode="false",
    )
    tree = ET.SubElement(root, "Tree", activeSpec="1")
    nodes = [
        "Sentinel#1",
        *(f"Sentinel-{key}#{selected[key]}" for key in ("49", "2") if key in selected),
    ]
    ET.SubElement(
        tree,
        "Spec",
        treeVersion=GAME_DATA,
        classId="2",
        ascendClassId="0",
        nodes=",".join(nodes),
    )
    for name in ("Items", "Skills", "Config"):
        ET.SubElement(root, name)
    return ET.tostring(root, encoding="unicode")


def verify_checkout(checkout: Path) -> None:
    if (
        not (checkout / "src" / "HeadlessWrapper.lua").is_file()
        or not (checkout / "runtime" / "lua").is_dir()
    ):
        raise ValueError(
            "LEB checkout requires src/HeadlessWrapper.lua and runtime/lua"
        )
    for args, expected in (
        (["rev-parse", "HEAD"], REVISION),
        (
            ["status", "--porcelain", "--untracked-files=all", "--", "src", "runtime"],
            "",
        ),
    ):
        result = subprocess.run(
            ["git", "-C", str(checkout), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode or result.stdout.strip() != expected:
            raise ValueError(
                "LEB checkout revision or calculator sources differ from pinned revision"
            )


def evaluate(
    snapshot: BuildSnapshot,
    checkout: Path,
    root: Path = Path("artifacts"),
    timeout: float = 60,
) -> Path:
    selected = supported(snapshot)
    verify_checkout(checkout)
    xml = calculator_xml(snapshot.character["level"], selected)
    with tempfile.TemporaryDirectory(prefix="arpg-leb-") as temporary:
        isolated = Path(temporary) / "leb"
        shutil.copytree(checkout / "src", isolated / "src")
        shutil.copytree(checkout / "runtime", isolated / "runtime")
        try:
            output_path = Path(temporary) / "output.json"
            process = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "arpg_build_lab.evaluators.worker",
                    str(output_path),
                ],
                input=xml,
                capture_output=True,
                text=True,
                cwd=isolated / "src",
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ValueError(
                f"LEB calculation timed out after {timeout} seconds"
            ) from exc
        if process.returncode:
            raise ValueError(
                f"LEB calculation failed: {process.stderr.strip()[-2000:]}"
            )
        try:
            output = json.loads(output_path.read_text())
        except (ValueError, OSError) as exc:
            raise ValueError("LEB worker returned invalid output") from exc
    if output.get("loaded") != {
        "class_id": 2,
        "class_name": "Sentinel",
        "mastery_id": 0,
        "level": snapshot.character["level"],
        "target_version": GAME_DATA,
        "tree_version": GAME_DATA,
        "auto_level": False,
        "nodes": {
            "Sentinel": 1,
            **{f"Sentinel-{key}": points for key, points in selected.items()},
        },
        "skills": 0,
        "items": 0,
        "equipped": {},
        "combat_inputs": CONFIG_DEFAULTS,
    }:
        raise ValueError(
            f"LEB loaded class, level, version, passives, items, skills, or combat inputs differ from requested input: {output.get('loaded')}"
        )
    if output.get("rounding") is not True:
        raise ValueError("LEB expected LETools rounding configuration is unavailable")
    from arpg_build_lab.evaluators.worker import metrics_from_output

    metrics = metrics_from_output(output)
    location = (
        root
        / "1.4.7"
        / "evaluations"
        / f"leb-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
    )
    location.mkdir(parents=True, exist_ok=False)
    files = {
        "snapshot.json": canonical_bytes(snapshot.to_dict()) + b"\n",
        "calculator-input.xml": xml.encode(),
        "calculator-output.json": canonical_bytes(output) + b"\n",
        "diagnostics.json": canonical_bytes(
            {
                "worker_stdout": process.stdout,
                "worker_stderr": process.stderr,
                "timeout_seconds": timeout,
            }
        )
        + b"\n",
    }
    try:
        for name, content in files.items():
            (location / name).write_bytes(content)
        evaluation = BuildEvaluation(
            1,
            snapshot.schema_version,
            snapshot.game_version,
            snapshot.source_url,
            snapshot.source_id,
            snapshot.raw_sha256,
            sha256(canonical_bytes(snapshot.to_dict())),
            "last_epoch_building",
            EVALUATOR_VERSION,
            REVISION,
            APPLICATION_VERSION,
            GAME_DATA,
            output["runtime"],
            output["runtime_version"],
            {
                "letools_round_half_up": True,
                "calculator_defaults": CONFIG_DEFAULTS,
                "timeout_seconds": timeout,
            },
            metrics,
            {name: sha256(content) for name, content in files.items()},
        )
        (location / "evaluation.json").write_bytes(
            canonical_bytes(evaluation.to_dict()) + b"\n"
        )
        load(location)
    except Exception:
        shutil.rmtree(location)
        raise
    return location
