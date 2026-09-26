"""Run pinned LEB examples with synthetic saved imports on this host."""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from arpg_build_lab.datasets.manifest import load as load_dataset
from arpg_build_lab.domain.evaluation import canonical_bytes, load, sha256
from arpg_build_lab.domain.snapshot import BuildSnapshot
from arpg_build_lab.importers.cli import load as load_import
from arpg_build_lab.importers.cli import save
from arpg_build_lab.importers.letools import parse_build

URL = "https://www.lastepochtools.com/planner/ABC12345"
FIXTURES = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "arpg_build_lab"
    / "evaluators"
    / "tests"
    / "fixtures"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check real pinned LEB calculations")
    parser.add_argument("--leb-checkout", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)

        def command(run: Path) -> Path:
            process = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "arpg_build_lab.cli",
                    str(run),
                    "--leb-checkout",
                    str(args.leb_checkout),
                    "--output-root",
                    str(root),
                ],
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )
            if process.returncode:
                print(
                    f"Real LEB command failed for {run} (exit {process.returncode})",
                    file=sys.stderr,
                )
                if process.stdout.strip():
                    print(process.stdout.rstrip(), file=sys.stderr)
                if process.stderr.strip():
                    print(process.stderr.rstrip(), file=sys.stderr)
                raise SystemExit(process.returncode)
            assert "Calculator reference results for Last Epoch 1.4.7" in process.stdout
            assert (
                "health points" in process.stdout and "armour rating" in process.stdout
            )
            line = next(
                line
                for line in process.stdout.splitlines()
                if line.startswith("Saved evaluation: ")
            )
            return Path(line.removeprefix("Saved evaluation: "))

        results = []
        for fixture, expected in (
            ("sentinel-baseline.json", (206, 0)),
            ("sentinel-allocated.json", (236, 16)),
            ("sentinel-baseline.json", (206, 0)),
        ):
            raw = (FIXTURES / fixture).read_bytes()
            run = save(raw, parse_build(raw, URL), root)
            snapshot = load_import(run)
            location = command(run)
            result = load(location)
            actual = (
                result.metrics["health"]["value"],
                result.metrics["armour"]["value"],
            )
            assert actual == expected, (fixture, actual, expected)
            assert result.snapshot_sha256 == sha256(canonical_bytes(snapshot.to_dict()))
            assert result.raw_sha256 == snapshot.raw_sha256
            assert json.loads((location / "calculator-output.json").read_text())[
                "loaded"
            ]["nodes"] == {
                "Sentinel": 1,
                **({"Sentinel-49": 5, "Sentinel-2": 1} if expected[1] else {}),
            }
            results.append(result)
        mutated = results[0]
        baseline_raw = (FIXTURES / "sentinel-baseline.json").read_bytes()
        mutation_run = save(baseline_raw, parse_build(baseline_raw, URL), root)
        original = load_import(mutation_run)
        value = original.to_dict()
        value["passives"]["selected"] = {"49": 5, "2": 1}
        changed = BuildSnapshot.from_dict(value)
        (mutation_run / "snapshot.json").write_text(json.dumps(changed.to_dict()))
        changed_result = load(command(mutation_run))
        assert changed_result.raw_sha256 == mutated.raw_sha256
        assert changed_result.snapshot_sha256 != mutated.snapshot_sha256
        assert changed_result.metrics["health"]["value"] == 236
        assert changed_result.metrics["armour"]["value"] == 16
        seed_run = save(baseline_raw, parse_build(baseline_raw, URL), root)
        seed_files = {path.name: path.read_bytes() for path in seed_run.iterdir()}
        datasets = []
        dataset_dirs = []
        for _ in range(2):
            process = subprocess.run(
                [
                    str(Path(sys.executable).with_name("arpg-dataset")),
                    str(seed_run),
                    "--leb-checkout",
                    str(args.leb_checkout),
                    "--output-root",
                    str(root),
                ],
                capture_output=True,
                text=True,
                timeout=900,
                check=False,
            )
            if process.returncode:
                print(process.stdout.rstrip(), file=sys.stderr)
                print(process.stderr.rstrip(), file=sys.stderr)
                raise SystemExit(process.returncode)
            assert "Valid candidates: 19" in process.stdout
            assert "health points" in process.stdout
            assert "armour rating" in process.stdout
            path = Path(
                next(
                    line.removeprefix("Saved dataset: ")
                    for line in process.stdout.splitlines()
                    if line.startswith("Saved dataset: ")
                )
            )
            dataset_dirs.append(path)
            datasets.append(load_dataset(path))
        assert {
            path.name: path.read_bytes() for path in seed_run.iterdir()
        } == seed_files
        first = datasets[0]
        second = datasets[1]
        assert first.manifest["candidate_count"] == 19
        assert first.manifest["measured_calculator_seconds"] > 0
        assert first.manifest["seed"] == second.manifest["seed"]

        def ordered_results(dataset, path):
            return [
                (
                    record["snapshot_sha256"],
                    load(path / record["evaluation_path"]).metrics,
                )
                for record in dataset.manifest["candidates"]
            ]

        assert ordered_results(first, dataset_dirs[0]) == ordered_results(
            second, dataset_dirs[1]
        )
        metrics = {
            tuple(
                candidate.passives["selected"].get(key, 0) for key in ("49", "2")
            ): load(dataset_dirs[0] / record["evaluation_path"]).metrics
            for candidate, record in zip(
                first.candidates, first.manifest["candidates"], strict=True
            )
        }
        assert metrics[(0, 0)]["health"]["value"] == 206
        assert metrics[(0, 0)]["armour"]["value"] == 0
        assert metrics[(5, 1)]["health"]["value"] == 236
        assert metrics[(5, 1)]["armour"]["value"] == 16
        moved = root / "moved-dataset"
        shutil.copytree(dataset_dirs[0], moved)
        shutil.rmtree(seed_run)
        assert load_dataset(moved).manifest["candidate_count"] == 19
        print(
            f"Dataset real calculator evidence: 19 candidates, {first.manifest['measured_calculator_seconds']:.3f} seconds"
        )
    print(
        "OK: pinned LEB baseline, allocated, repeat, canonical mutation, dataset reload, retained hashes and loaded identity"
    )


if __name__ == "__main__":
    main()
