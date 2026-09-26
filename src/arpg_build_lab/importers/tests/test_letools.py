import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from arpg_build_lab.domain.snapshot import BuildSnapshot
from arpg_build_lab.importers.cli import load, save
from arpg_build_lab.importers.letools import ImportError, fetch, parse_build, planner_id

URL = "https://www.lastepochtools.com/planner/ABC12345"


def response():
    return {
        "created_for_build": "Version 1.5.0",
        "data_version": "Version 1.5.0",
        "data": {
            "dataVersion": "Version 1.5.0",
            "bio": {"level": 42, "characterClass": 3, "chosenMastery": 1},
            "charTree": {"treeID": "", "selected": {"4": 0, "5": 2}, "version": 1},
            "skillTrees": [
                {
                    "treeID": "abc",
                    "selected": {"1": 0, "2": 3},
                    "level": 5,
                    "slotNumber": 0,
                    "version": 2,
                }
            ],
            "equipment": {
                "head": {
                    "id": "UNKNOWN_ITEM",
                    "ir": 7,
                    "ur": 9,
                    "affixes": [
                        {"id": "UNKNOWN_AFFIX", "tier": 4},
                        {"id": "AAzDMQ", "tier": 5, "r": 12},
                    ],
                    "sealedAffix": {"id": "UNKNOWN_SEALED", "tier": 1},
                    "primordialAffix": {"id": "UNKNOWN_PRIMORDIAL", "tier": 2},
                    "corruptedAffix": {"id": "UNKNOWN_CORRUPTED", "tier": 3},
                }
            },
            "idols": [{"x": 2, "y": 3, "id": "UNKNOWN_IDOL", "affixes": []}],
            "blessings": {"1": {"id": "BLESSING", "extra": True}},
            "completedQuests": [1, 2],
        },
    }


def raw(value):
    return json.dumps(value).encode()


class ImportTests(unittest.TestCase):
    def test_shared_artifact_root_across_worktrees_and_explicit_override(self):
        payload = raw(response())
        snapshot = parse_build(payload, URL)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shared = root / "shared"
            first_worktree = root / "first-worktree"
            second_worktree = root / "second-worktree"
            first_worktree.mkdir()
            second_worktree.mkdir()
            raw_path = root / "response.json"
            raw_path.write_bytes(payload)
            command = Path(sys.executable).with_name("arpg-import")
            for worktree in (first_worktree, second_worktree):
                process = subprocess.run(
                    [str(command), URL, "--raw-file", str(raw_path)],
                    cwd=worktree,
                    env={**os.environ, "ARPG_BUILD_LAB_ARTIFACTS_ROOT": str(shared)},
                    capture_output=True,
                    text=True,
                    check=True,
                )
                saved_path = Path(
                    next(
                        line.removeprefix("Saved import: ")
                        for line in process.stdout.splitlines()
                        if line.startswith("Saved import: ")
                    )
                )
                self.assertTrue(saved_path.is_relative_to(shared))
                self.assertEqual(load(saved_path), snapshot)
            runs = list((shared / "1.5.0/imports").iterdir())
            self.assertEqual(len(runs), 2)
            self.assertTrue(all(load(run) == snapshot for run in runs))
            subprocess.run(
                [str(command), URL, "--raw-file", str(raw_path)],
                cwd=first_worktree,
                env={**os.environ, "ARPG_BUILD_LAB_ARTIFACTS_ROOT": "relative"},
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(
                len(list((first_worktree / "relative/1.5.0/imports").iterdir())), 1
            )
            subprocess.run(
                [str(command), URL, "--raw-file", str(raw_path)],
                cwd=second_worktree,
                env={**os.environ, "ARPG_BUILD_LAB_ARTIFACTS_ROOT": ""},
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(
                len(list((second_worktree / "artifacts/1.5.0/imports").iterdir())),
                1,
            )
            explicit = root / "explicit"
            subprocess.run(
                [
                    str(command),
                    URL,
                    "--raw-file",
                    str(raw_path),
                    "--output-root",
                    str(explicit),
                ],
                cwd=second_worktree,
                env={**os.environ, "ARPG_BUILD_LAB_ARTIFACTS_ROOT": str(shared)},
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(len(list((explicit / "1.5.0/imports").iterdir())), 1)
            with patch.dict(
                os.environ, {"ARPG_BUILD_LAB_ARTIFACTS_ROOT": str(root / "one")}
            ):
                first = save(payload, snapshot)
                os.environ["ARPG_BUILD_LAB_ARTIFACTS_ROOT"] = str(root / "two")
                second = save(payload, snapshot)
                third = save(payload, snapshot, root / "explicit-public")
            self.assertTrue(first.is_relative_to(root / "one"))
            self.assertTrue(second.is_relative_to(root / "two"))
            self.assertTrue(third.is_relative_to(root / "explicit-public"))
            self.assertEqual(load(second), snapshot)

    def test_parse_build_and_round_trip(self):
        payload = raw(response())
        snapshot = parse_build(payload, URL)
        self.assertEqual(snapshot.game_version, "1.5.0")
        self.assertEqual(snapshot.passives["selected"], {"4": 0, "5": 2})
        self.assertEqual(snapshot.skills[0]["level"], 5)
        head = snapshot.equipment["head"]
        self.assertIsNone(head["translation"])
        self.assertEqual(head["source_fields"]["ir"], 7)
        self.assertEqual(head["affixes"][0]["roll"], None)
        self.assertEqual(head["affixes"][1]["roll"], 12)
        self.assertEqual(
            set(head["special_affixes"]),
            {"sealedAffix", "primordialAffix", "corruptedAffix"},
        )
        self.assertEqual(snapshot.idols[0]["x"], 2)
        self.assertEqual(snapshot.blessings["1"]["source_fields"]["extra"], True)
        self.assertEqual(
            snapshot.unresolved["item_ids"], ["UNKNOWN_IDOL", "UNKNOWN_ITEM"]
        )
        self.assertEqual(snapshot.unresolved["blessing_ids"], ["BLESSING"])
        self.assertEqual(snapshot.unsupported_sections, ["data.completedQuests"])
        with tempfile.TemporaryDirectory() as temp:
            location = save(payload, snapshot, Path(temp))
            self.assertEqual(load(location), snapshot)
            self.assertEqual((location / "raw.json").read_bytes(), payload)
            (location / "raw.json").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash"):
                load(location)

    def test_missing_and_conflicting_versions(self):
        value = response()
        del value["created_for_build"]
        with tempfile.TemporaryDirectory() as temp:
            snapshot = parse_build(raw(value), URL)
            self.assertIsNone(snapshot.game_version)
            self.assertIn(
                "/unknown/imports/", str(save(raw(value), snapshot, Path(temp)))
            )
        value["created_for_build"] = "Version 1.4.0"
        self.assertIsNone(parse_build(raw(value), URL).game_version)
        value["created_for_build"] = 150
        with self.assertRaisesRegex(ImportError, "created_for_build"):
            parse_build(raw(value), URL)

    def test_known_translations_and_missing_roll(self):
        value = response()
        value["data"]["equipment"]["head"]["id"] = "UAzCMNI"
        value["data"]["equipment"]["head"]["affixes"][1]["r"] = 0
        value["data"]["blessings"]["1"]["id"] = "IIwBgzALMwSdA"
        snapshot = parse_build(raw(value), URL)
        self.assertEqual(snapshot.equipment["head"]["translation"]["base_type_id"], 0)
        self.assertEqual(snapshot.equipment["head"]["translation"]["sub_type_id"], 1)
        self.assertEqual(snapshot.equipment["head"]["translation"]["unique_id"], 1)
        self.assertEqual(snapshot.equipment["head"]["affixes"][1]["translated_id"], 3)
        self.assertIsNone(snapshot.equipment["head"]["affixes"][0]["roll"])
        self.assertEqual(snapshot.equipment["head"]["affixes"][1]["roll"], 0)
        self.assertEqual(snapshot.blessings["1"]["translation"]["base_type_id"], 34)
        self.assertEqual(
            snapshot.blessings["1"]["source_namespace"], "letools.blessing"
        )
        self.assertEqual(snapshot.unresolved["blessing_ids"], [])

    def test_invalid_imported_scalars_and_persisted_records(self):
        changes = [
            (lambda v: v["data"]["bio"].update(level={"bad": True}), "character.level"),
            (
                lambda v: v["data"]["bio"].update(characterClass=True),
                "character.class_id",
            ),
            (
                lambda v: v["data"]["equipment"]["head"]["affixes"][0].update(
                    tier="five"
                ),
                "tier",
            ),
            (
                lambda v: v["data"]["equipment"]["head"]["affixes"][0].update(r=True),
                "roll",
            ),
            (lambda v: v["data"]["idols"][0].update(x="2"), "idols\\[0\\].x"),
            (
                lambda v: v["data"]["blessings"]["1"].update(id={"bad": True}),
                "blessings.1.id",
            ),
            (
                lambda v: v["data"]["equipment"]["head"].update(ir="7"),
                "equipment.head.ir",
            ),
        ]
        for mutate, path in changes:
            with self.subTest(path=path):
                value = response()
                mutate(value)
                with self.assertRaisesRegex(ImportError, path):
                    parse_build(raw(value), URL)
        with self.assertRaisesRegex(ImportError, "valid JSON"):
            parse_build(raw(response()).replace(b'"level": 42', b'"level": NaN'), URL)
        snapshot = parse_build(raw(response()), URL)
        persisted = snapshot.to_dict()
        bad = copy.deepcopy(persisted)
        bad["skills"][0]["selected"]["1"] = "many"
        with self.assertRaisesRegex(ValueError, "skills\\[0\\].selected.1"):
            BuildSnapshot.from_dict(bad)
        bad = copy.deepcopy(persisted)
        bad["blessings"]["1"]["source_id"] = 123
        with self.assertRaisesRegex(ValueError, "blessings.1.source_id"):
            BuildSnapshot.from_dict(bad)
        bad = copy.deepcopy(persisted)
        bad["equipment"]["head"]["affixes"][0]["roll"] = float("nan")
        with self.assertRaisesRegex(ValueError, "roll"):
            BuildSnapshot.from_dict(bad)
        bad = copy.deepcopy(persisted)
        bad["version_evidence"]["created_for_build"] = 150
        with self.assertRaisesRegex(ValueError, "version_evidence.created_for_build"):
            BuildSnapshot.from_dict(bad)
        bad = copy.deepcopy(persisted)
        bad["raw_sha256"] = "wrong"
        with self.assertRaisesRegex(ValueError, "raw_sha256"):
            BuildSnapshot.from_dict(bad)

    def test_snapshot_version_evidence_is_independent_of_source_field_names(self):
        persisted = parse_build(raw(response()), URL).to_dict()
        persisted["version_evidence"] = {"recorded_game_version": "1.5.0"}
        snapshot = BuildSnapshot.from_dict(persisted)
        self.assertEqual(
            snapshot.to_dict()["version_evidence"], {"recorded_game_version": "1.5.0"}
        )

    def test_rejects_bad_inputs(self):
        for url in (
            "http://www.lastepochtools.com/planner/ABC12345",
            "https://other.test/planner/ABC12345",
            "https://www.lastepochtools.com/planner/ABC12345?x=1",
            "https://www.lastepochtools.com/planner/../../x",
        ):
            with self.subTest(url=url), self.assertRaises(ImportError):
                planner_id(url)
        with self.assertRaisesRegex(ImportError, "valid JSON"):
            parse_build(b"{", URL)
        with self.assertRaisesRegex(ImportError, "data"):
            parse_build(raw({"data": []}), URL)
        value = response()
        value["data"]["skillTrees"][0]["selected"]["1"] = "many"
        with self.assertRaisesRegex(ImportError, "integer allocation"):
            parse_build(raw(value), URL)

    def test_fetch_errors_and_single_endpoint(self):
        error = HTTPError("", 403, "Forbidden", {}, None)
        with patch("urllib.request.OpenerDirector.open", side_effect=error):
            with self.assertRaisesRegex(ImportError, "HTTP 403"):
                fetch(URL)
        error.close()
        with patch(
            "urllib.request.OpenerDirector.open", side_effect=URLError("timed out")
        ):
            with self.assertRaisesRegex(ImportError, "timed out"):
                fetch(URL)
        redirect = HTTPError(
            "", 302, "Found", {"Location": "https://elsewhere.test/"}, None
        )
        with patch(
            "urllib.request.OpenerDirector.open", side_effect=redirect
        ) as opened:
            with self.assertRaisesRegex(ImportError, "HTTP 302"):
                fetch(URL)
            opened.assert_called_once()
        redirect.close()

    def test_successful_request_uses_single_public_endpoint(self):
        with patch(
            "urllib.request.OpenerDirector.open", return_value=BytesIO(b"{}")
        ) as opened:
            self.assertEqual(fetch(URL, timeout=7), b"{}")
            opened.assert_called_once()
            request = opened.call_args.args[0]
            self.assertEqual(
                request.full_url,
                "https://www.lastepochtools.com/api/public/build_data/ABC12345",
            )
            self.assertIn("Mozilla/5.0", request.get_header("User-agent"))
            self.assertEqual(opened.call_args.kwargs["timeout"], 7)


if __name__ == "__main__":
    unittest.main()
