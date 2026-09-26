"""Generate an exhaustive reference dataset from one saved Sentinel import."""

import argparse
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from arpg_build_lab.datasets.manifest import CONFIGURATION, load, snapshot_hash
from arpg_build_lab.datasets.passive_space import GENERATOR_VERSION, candidates
from arpg_build_lab.domain.evaluation import canonical_bytes, sha256
from arpg_build_lab.domain.evaluation import load as load_evaluation
from arpg_build_lab.evaluators.le_building import (
    evaluate,
    supported,
    verify_checkout,
)
from arpg_build_lab.importers.cli import load as load_import
from arpg_build_lab.importers.letools import validate_evaluation_source


def generate(
    import_run: Path,
    checkout: Path,
    root: Path = Path("artifacts"),
    timeout: float = 60,
) -> Path:
    if not 0 < timeout <= 600:
        raise ValueError("timeout must be greater than 0 and no more than 600 seconds")
    seed = load_import(import_run)
    validate_evaluation_source((import_run / seed.raw_path).read_bytes(), seed)
    supported(seed)
    verify_checkout(checkout)
    planned = candidates(seed)
    run_id = f"sentinel-passives-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
    location = root / "1.4.7" / "datasets" / run_id
    location.mkdir(parents=True, exist_ok=False)
    seed_dir = location / "seed"
    seed_dir.mkdir()
    for name in ("snapshot.json", seed.raw_path, "provenance.json"):
        source = import_run / name
        if source.is_file():
            target = seed_dir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    records = []
    total_seconds = 0.0
    evaluator_identity = None
    for index, snapshot in enumerate(planned):
        selected = snapshot.passives["selected"]
        print(
            f"Calculating {index + 1}/{len(planned)}: Fearless {selected.get('49', 0)}, Armour Clad {selected.get('2', 0)}",
            flush=True,
        )
        started = time.monotonic()
        try:
            evaluation_dir = evaluate(
                snapshot, checkout, location / "_working", timeout
            )
            total_seconds += time.monotonic() - started
            evaluation = load_evaluation(evaluation_dir)
            target = location / "candidates" / f"{index:03d}"
            target.parent.mkdir(exist_ok=True)
            shutil.move(str(evaluation_dir), target)
            identity = {
                "name": evaluation.evaluator,
                "version": evaluation.evaluator_version,
                "calculator_revision": evaluation.calculator_revision,
                "calculator_application_version": evaluation.calculator_application_version,
                "calculator_game_data": evaluation.calculator_game_data,
                "configuration": evaluation.configuration,
            }
            if evaluator_identity is not None and evaluator_identity != identity:
                raise ValueError(
                    "Calculator identity or configuration changed within run"
                )
            evaluator_identity = identity
            records.append(
                {
                    "index": index,
                    "snapshot_sha256": snapshot_hash(snapshot),
                    "evaluation_path": f"candidates/{index:03d}",
                    "evaluation_sha256": sha256(
                        (target / "evaluation.json").read_bytes()
                    ),
                }
            )
        except Exception as exc:
            raise ValueError(
                f"Candidate {index} (Fearless {selected.get('49', 0)}, Armour Clad {selected.get('2', 0)}) failed: {exc}"
            ) from exc
    shutil.rmtree(location / "_working")
    manifest = {
        "schema_version": 1,
        "snapshot_schema_version": seed.schema_version,
        "evaluation_schema_version": 1,
        "game_version": seed.game_version,
        "seed": {
            "path": "seed",
            "snapshot_sha256": snapshot_hash(seed),
            "source_url": seed.source_url,
            "source_id": seed.source_id,
            "raw_sha256": seed.raw_sha256,
            "provenance_sha256": (
                sha256((seed_dir / "provenance.json").read_bytes())
                if (seed_dir / "provenance.json").is_file()
                else None
            ),
        },
        "generator": {
            "name": "sentinel_passive_space",
            "version": GENERATOR_VERSION,
            "configuration": CONFIGURATION,
        },
        "evaluator": evaluator_identity,
        "candidate_count": len(records),
        "candidates": records,
        "measured_calculator_seconds": total_seconds,
    }
    path = location / "manifest.json"
    try:
        path.write_bytes(canonical_bytes(manifest) + b"\n")
        load(location)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return location


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate calculator reference results for every supported passive allocation"
    )
    parser.add_argument("import_run", type=Path, help="Existing import-run directory")
    parser.add_argument("--leb-checkout", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts"))
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args(argv)
    try:
        location = generate(
            args.import_run, args.leb_checkout, args.output_root, args.timeout
        )
        dataset = load(location)
    except (OSError, ValueError) as exc:
        print(f"Dataset failed for {args.import_run}: {exc}", file=sys.stderr)
        return 1
    evaluations = [
        load_evaluation(location / record["evaluation_path"])
        for record in dataset.manifest["candidates"]
    ]
    for name, unit in (("health", "health points"), ("armour", "armour rating")):
        values = [evaluation.metrics[name]["value"] for evaluation in evaluations]
        print(
            f"{name.capitalize()} calculator reference range: {min(values)} to {max(values)} {unit}"
        )
    print(f"Valid candidates: {len(evaluations)}")
    print(
        f"Measured total calculator time: {dataset.manifest['measured_calculator_seconds']:.3f} seconds"
    )
    print(f"Saved dataset: {location}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
