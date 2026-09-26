import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from arpg_build_lab.datasets.cli import generate
from arpg_build_lab.datasets.manifest import load, snapshot_hash
from arpg_build_lab.datasets.passive_space import candidates
from arpg_build_lab.domain.evaluation import BuildEvaluation, canonical_bytes, sha256
from arpg_build_lab.domain.snapshot import BuildSnapshot
from arpg_build_lab.importers.cli import load as load_import
from arpg_build_lab.importers.cli import save
from arpg_build_lab.importers.letools import parse_build

URL = "https://www.lastepochtools.com/planner/ABC12345"
FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "evaluators/tests/fixtures/sentinel-baseline.json"
)


def saved(root: Path) -> Path:
    raw = FIXTURE.read_bytes()
    return save(raw, parse_build(raw, URL), root)


def at_level(seed: BuildSnapshot, level: int) -> BuildSnapshot:
    value = seed.to_dict()
    value["character"]["level"] = level
    value["character"]["source_fields"]["level"] = level
    return BuildSnapshot.from_dict(value)


def fake_evaluate(
    snapshot: BuildSnapshot, checkout: Path, root: Path, timeout: float
) -> Path:
    selected = snapshot.passives["selected"]
    location = root / "1.4.7/evaluations/fake"
    location.mkdir(parents=True)
    files = {
        "snapshot.json": canonical_bytes(snapshot.to_dict()) + b"\n",
        "calculator-input.xml": b"<input/>",
        "calculator-output.json": b"{}",
        "diagnostics.json": b"{}",
    }
    for name, data in files.items():
        (location / name).write_bytes(data)
    evaluation = BuildEvaluation(
        1,
        1,
        "1.4.7",
        snapshot.source_url,
        snapshot.source_id,
        snapshot.raw_sha256,
        snapshot_hash(snapshot),
        "last_epoch_building",
        "1",
        "a97d388aca0da00907afb9d5a945c8f254a67b18",
        "0.14.0",
        "1_4",
        "fake",
        "1",
        {"timeout_seconds": timeout},
        {
            "health": {"value": 206 + selected.get("49", 0), "unit": "health points"},
            "armour": {"value": selected.get("2", 0), "unit": "armour rating"},
        },
        {name: sha256(data) for name, data in files.items()},
    )
    (location / "evaluation.json").write_bytes(
        canonical_bytes(evaluation.to_dict()) + b"\n"
    )
    return location


class DatasetTests(unittest.TestCase):
    def test_boundaries_order_and_preserved_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            seed = load_import(saved(Path(temporary)))
            for level, count in ((1, 1), (10, 19), (14, 29), (100, 29)):
                with self.subTest(level=level):
                    original = at_level(seed, level)
                    result = candidates(original)
                    self.assertEqual(len(result), count)
                    self.assertEqual(result, candidates(original))
                    self.assertEqual(result[0].passives["selected"], {})
                    self.assertEqual(
                        [
                            (
                                item.passives["selected"].get("49", 0),
                                item.passives["selected"].get("2", 0),
                            )
                            for item in result
                        ],
                        sorted(
                            (
                                item.passives["selected"].get("49", 0),
                                item.passives["selected"].get("2", 0),
                            )
                            for item in result
                        ),
                    )
                    self.assertEqual(
                        len({snapshot_hash(item) for item in result}), count
                    )
                    for item in result:
                        self.assertEqual(
                            item.to_dict() | {"passives": original.passives},
                            original.to_dict(),
                        )
                        self.assertTrue(all(item.passives["selected"].values()))
            value = seed.to_dict()
            value["passives"]["selected"] = {"49": 0, "2": 0}
            zero_seed = BuildSnapshot.from_dict(value)
            self.assertEqual(candidates(zero_seed)[0].passives["selected"], {})
            self.assertEqual(len(candidates(zero_seed)), 19)

    def test_complete_relocation_and_corruption_rejection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            import_run = saved(root)
            original = {path.name: path.read_bytes() for path in import_run.iterdir()}
            with (
                patch("arpg_build_lab.datasets.cli.verify_checkout"),
                patch(
                    "arpg_build_lab.datasets.cli.evaluate", side_effect=fake_evaluate
                ),
            ):
                location = generate(import_run, root / "checkout", root)
            self.assertEqual(
                {path.name: path.read_bytes() for path in import_run.iterdir()},
                original,
            )
            moved = root / "moved"
            shutil.copytree(location, moved)
            shutil.rmtree(import_run)
            dataset = load(moved)
            self.assertEqual(len(dataset.candidates), 19)
            self.assertEqual(dataset.seed.source_id, dataset.candidates[0].source_id)
            self.assertEqual(
                len(
                    {
                        record["snapshot_sha256"]
                        for record in dataset.manifest["candidates"]
                    }
                ),
                19,
            )

            def corrupt(path: Path, content: bytes, diagnostic: str):
                old = path.read_bytes()
                path.write_bytes(content)
                try:
                    with self.assertRaisesRegex((ValueError, OSError), diagnostic):
                        load(moved)
                finally:
                    path.write_bytes(old)

            corrupt(moved / "seed/raw.json", b"{}", "raw response hash")
            corrupt(moved / "seed/provenance.json", b"{}", "provenance")
            corrupt(
                moved / "candidates/000/calculator-output.json", b"bad", "file hash"
            )
            (moved / "candidates/019").mkdir()
            with self.assertRaisesRegex(ValueError, "directories differ"):
                load(moved)
            (moved / "candidates/019").rmdir()
            manifest_path = moved / "manifest.json"
            manifest = dataset.manifest
            for field in (
                "schema_version",
                "snapshot_schema_version",
                "evaluation_schema_version",
            ):
                for invalid in (True, 1.0):
                    with self.subTest(field=field, invalid=invalid):
                        value = json.loads(json.dumps(manifest))
                        value[field] = invalid
                        corrupt(
                            manifest_path,
                            canonical_bytes(value),
                            "schema or game version",
                        )
            for change, diagnostic in (
                (lambda value: value["candidates"].pop(), "count or coverage"),
                (
                    lambda value: value["candidates"].__setitem__(
                        1, value["candidates"][0]
                    ),
                    "record is invalid",
                ),
                (
                    lambda value: value["candidates"][0].update(
                        snapshot_sha256="0" * 64
                    ),
                    "snapshot differs",
                ),
                (
                    lambda value: value["candidates"][0].update(
                        evaluation_sha256="0" * 64
                    ),
                    "evaluation record hash",
                ),
            ):
                value = json.loads(json.dumps(manifest))
                change(value)
                corrupt(manifest_path, canonical_bytes(value), diagnostic)

    def test_invalid_seed_and_midrun_failure_never_publish_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            import_run = saved(root)
            value = json.loads((import_run / "snapshot.json").read_text())
            value["passives"]["selected"] = {"2": 1}
            (import_run / "snapshot.json").write_text(json.dumps(value))
            with (
                patch("arpg_build_lab.datasets.cli.verify_checkout"),
                patch("arpg_build_lab.datasets.cli.evaluate") as evaluate,
            ):
                with self.assertRaisesRegex(ValueError, "Armour Clad"):
                    generate(import_run, root / "checkout", root)
                evaluate.assert_not_called()
            self.assertFalse((root / "1.4.7/datasets").exists())
            (import_run / "snapshot.json").write_text(
                json.dumps(load_import(saved(root)).to_dict())
            )
            calls = 0

            def failing(snapshot, checkout, output, timeout):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise ValueError("injected failure")
                return fake_evaluate(snapshot, checkout, output, timeout)

            with (
                patch("arpg_build_lab.datasets.cli.verify_checkout"),
                patch("arpg_build_lab.datasets.cli.evaluate", side_effect=failing),
            ):
                with self.assertRaisesRegex(
                    ValueError, "Candidate 2.*injected failure"
                ):
                    generate(import_run, root / "checkout", root)
            self.assertEqual(calls, 3)
            self.assertFalse(list((root / "1.4.7/datasets").glob("*/manifest.json")))
