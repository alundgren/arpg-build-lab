import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from arpg_build_lab.domain.evaluation import (
    BuildEvaluation,
    canonical_bytes,
    load,
    sha256,
)
from arpg_build_lab.domain.snapshot import BuildSnapshot
from arpg_build_lab.evaluators.le_building import calculator_xml, supported
from arpg_build_lab.evaluators.worker import metrics_from_output
from arpg_build_lab.importers.cli import load as load_import
from arpg_build_lab.importers.cli import save
from arpg_build_lab.importers.letools import parse_build, validate_evaluation_source

URL = "https://www.lastepochtools.com/planner/ABC12345"
FIXTURE = Path(__file__).parent / "fixtures" / "sentinel-baseline.json"


def saved(root: Path) -> Path:
    raw = FIXTURE.read_bytes()
    return save(raw, parse_build(raw, URL), root)


class EvaluationTests(unittest.TestCase):
    def test_saved_version_evidence_and_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            location = saved(Path(temporary))
            snapshot = json.loads((location / "snapshot.json").read_text())
            snapshot["game_version"] = "1.5.0"
            (location / "snapshot.json").write_text(json.dumps(snapshot))
            with self.assertRaisesRegex(ValueError, "game_version"):
                load_import(location)
            snapshot["game_version"] = "1.4.7"
            snapshot["version_evidence"]["created_for_build"] = "Version 1.5.0"
            (location / "snapshot.json").write_text(json.dumps(snapshot))
            with self.assertRaisesRegex(ValueError, "version_evidence"):
                load_import(location)
            snapshot["version_evidence"]["created_for_build"] = "Version 1.4.7"
            (location / "snapshot.json").write_text(json.dumps(snapshot))
            provenance = json.loads((location / "provenance.json").read_text())
            provenance["game_version"] = "1.5.0"
            (location / "provenance.json").write_text(json.dumps(provenance))
            with self.assertRaisesRegex(ValueError, "provenance game_version"):
                load_import(location)
            newer = json.loads(FIXTURE.read_text())
            newer["created_for_build"] = "Version 1.5.0"
            newer["data_version"] = "Version 1.5.0"
            newer["data"]["dataVersion"] = "Version 1.5.0"
            raw = json.dumps(newer).encode()
            newer_run = save(raw, parse_build(raw, URL), Path(temporary))
            claimed = json.loads((newer_run / "snapshot.json").read_text())
            claimed["game_version"] = "1.4.7"
            claimed["version_evidence"] = {
                key: "Version 1.4.7" for key in claimed["version_evidence"]
            }
            (newer_run / "snapshot.json").write_text(json.dumps(claimed))
            with self.assertRaisesRegex(ValueError, "version_evidence"):
                load_import(newer_run)

    def test_raw_content_cannot_be_silently_discarded(self):
        with tempfile.TemporaryDirectory() as temporary:
            location = saved(Path(temporary))
            snapshot = load_import(location)
            raw = json.loads((location / "raw.json").read_text())
            validate_evaluation_source((location / "raw.json").read_bytes(), snapshot)
            changed_snapshot = snapshot.to_dict()
            changed_snapshot["character"]["source_fields"]["chosenMastery"] = False
            with self.assertRaisesRegex(ValueError, "chosenMastery.*integers"):
                validate_evaluation_source(
                    (location / "raw.json").read_bytes(),
                    BuildSnapshot.from_dict(changed_snapshot),
                )
            for key, value in (
                ("completedQuests", [1]),
                ("skillTrees", [{"treeID": "x"}]),
            ):
                changed = copy.deepcopy(raw)
                changed["data"][key] = value
                with (
                    self.subTest(key=key),
                    self.assertRaisesRegex(ValueError, f"data.{key}"),
                ):
                    validate_evaluation_source(json.dumps(changed).encode(), snapshot)
            raw["data"]["charTree"]["extra"] = True
            with self.assertRaisesRegex(ValueError, "charTree"):
                validate_evaluation_source(json.dumps(raw).encode(), snapshot)

    def test_supported_content_and_canonical_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            baseline = load_import(saved(Path(temporary)))
            self.assertEqual(supported(baseline), {})
            self.assertIn('nodes="Sentinel#1"', calculator_xml(10, {}))
            value = baseline.to_dict()
            value["passives"]["selected"] = {"49": 5, "2": 1}
            allocated = BuildSnapshot.from_dict(value)
            self.assertEqual(supported(allocated), {"49": 5, "2": 1})
            self.assertNotEqual(
                sha256(canonical_bytes(baseline.to_dict())),
                sha256(canonical_bytes(allocated.to_dict())),
            )
            self.assertIn("Sentinel-49#5", calculator_xml(10, supported(allocated)))
            self.assertEqual(baseline.raw_sha256, allocated.raw_sha256)
            cases = [
                (lambda v: v.update(game_version="1.5.0"), "game_version"),
                (lambda v: v["character"].update(class_id=3), "class_id"),
                (lambda v: v["character"].update(mastery_id=1), "mastery_id"),
                (lambda v: v["character"].update(level=0), "level"),
                (lambda v: v["passives"]["selected"].update({"49": 9}), "49"),
                (lambda v: v["passives"]["selected"].update({"2": 1}), "Armour Clad"),
                (lambda v: v["passives"]["selected"].update({"99": 1}), "Fearless"),
                (lambda v: v["passives"].update(source_namespace="other"), "passives"),
                (lambda v: v["skills"].append({}), "skills"),
                (
                    lambda v: v["unsupported_sections"].append("data.quests"),
                    "unsupported_sections",
                ),
                (lambda v: v["unresolved"]["item_ids"].append("x"), "unresolved"),
                (
                    lambda v: v["character"]["source_fields"].update(extra=1),
                    "source_fields",
                ),
                (
                    lambda v: v["character"]["source_fields"].update(
                        chosenMastery=False
                    ),
                    "source_fields",
                ),
            ]
            for change, diagnostic in cases:
                modified = copy.deepcopy(baseline.to_dict())
                change(modified)
                with (
                    self.subTest(diagnostic=diagnostic),
                    self.assertRaisesRegex(ValueError, diagnostic),
                ):
                    supported(BuildSnapshot(**modified))

    def test_metrics_and_result_validation(self):
        self.assertEqual(
            metrics_from_output({"metrics": {"Life": 206, "Armour": 0}})["armour"][
                "value"
            ],
            0,
        )
        for bad in (None, -1, float("nan"), float("inf"), "0", True):
            with self.subTest(value=bad), self.assertRaisesRegex(ValueError, "Armour"):
                metrics_from_output({"metrics": {"Life": 206, "Armour": bad}})
        with self.assertRaisesRegex(ValueError, "Life"):
            metrics_from_output({"metrics": {"Armour": 0}})
        with self.assertRaisesRegex(ValueError, "schema"):
            BuildEvaluation.from_dict({})
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises((OSError, ValueError)):
                load(Path(temporary))

    def test_retained_file_hashes_and_source_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = load_import(saved(root))
            location = root / "evaluation"
            location.mkdir()
            files = {
                "snapshot.json": canonical_bytes(snapshot.to_dict()),
                "calculator-input.xml": b"<LastEpochBuilding />",
                "calculator-output.json": b"{}",
                "diagnostics.json": b"{}",
            }
            for name, content in files.items():
                (location / name).write_bytes(content)
            evaluation = BuildEvaluation(
                1,
                1,
                "1.4.7",
                snapshot.source_url,
                snapshot.source_id,
                snapshot.raw_sha256,
                sha256(canonical_bytes(snapshot.to_dict())),
                "last_epoch_building",
                "1",
                "revision",
                "0.14.0",
                "1_4",
                "Lupa LuaJIT 2.1",
                "2.8",
                {},
                {
                    "health": {"value": 206, "unit": "health points"},
                    "armour": {"value": 0, "unit": "armour rating"},
                },
                {name: sha256(content) for name, content in files.items()},
            )
            (location / "evaluation.json").write_bytes(
                canonical_bytes(evaluation.to_dict())
            )
            self.assertEqual(load(location), evaluation)
            malformed = evaluation.to_dict()
            malformed["metrics"]["health"]["value"] = 10**400
            with self.assertRaisesRegex(ValueError, "Invalid health value"):
                BuildEvaluation.from_dict(malformed)
            (location / "calculator-output.json").write_bytes(b'{"Life":0}')
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                load(location)

    def test_missing_checkout_and_timeout(self):
        from arpg_build_lab.evaluators.le_building import evaluate

        with tempfile.TemporaryDirectory() as temporary:
            snapshot = load_import(saved(Path(temporary)))
            with self.assertRaisesRegex(ValueError, "checkout"):
                evaluate(snapshot, Path(temporary))
            with (
                patch("arpg_build_lab.evaluators.le_building.verify_checkout"),
                patch("arpg_build_lab.evaluators.le_building.shutil.copytree"),
                patch(
                    "arpg_build_lab.evaluators.le_building.subprocess.run",
                    side_effect=subprocess.TimeoutExpired("worker", 0.1),
                ),
            ):
                with self.assertRaisesRegex(ValueError, "timed out"):
                    evaluate(snapshot, Path(temporary), timeout=0.1)
            with (
                patch("arpg_build_lab.evaluators.le_building.verify_checkout"),
                patch("arpg_build_lab.evaluators.le_building.shutil.copytree"),
                patch(
                    "arpg_build_lab.evaluators.le_building.subprocess.run",
                    return_value=subprocess.CompletedProcess(
                        "worker", 1, "", "No module named lupa"
                    ),
                ),
            ):
                with self.assertRaisesRegex(ValueError, "No module named lupa"):
                    evaluate(snapshot, Path(temporary))
