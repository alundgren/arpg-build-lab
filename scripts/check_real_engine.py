"""Run pinned LEB examples with synthetic saved imports on this host."""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

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
                check=True,
            )
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
    print(
        "OK: pinned LEB baseline, allocated, repeat, canonical mutation, retained hashes and loaded identity"
    )


if __name__ == "__main__":
    main()
