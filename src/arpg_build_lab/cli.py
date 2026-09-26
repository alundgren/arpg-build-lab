"""Run a supported saved import through Last Epoch Building."""

import argparse
import sys
from pathlib import Path

from arpg_build_lab.domain.evaluation import load as load_evaluation
from arpg_build_lab.evaluators.le_building import evaluate
from arpg_build_lab.importers.cli import load as load_import
from arpg_build_lab.importers.letools import validate_evaluation_source


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a saved 1.4.7 Sentinel build with a local pinned Last Epoch Building checkout"
    )
    parser.add_argument("import_run", type=Path, help="Existing import-run directory")
    parser.add_argument(
        "--leb-checkout",
        type=Path,
        required=True,
        help="Local pinned Last Epoch Building checkout",
    )
    parser.add_argument("--output-root", type=Path, default=Path("artifacts"))
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args(argv)
    try:
        if not 0 < args.timeout <= 600:
            raise ValueError(
                "timeout must be greater than 0 and no more than 600 seconds"
            )
        snapshot = load_import(args.import_run)
        validate_evaluation_source(
            (args.import_run / snapshot.raw_path).read_bytes(), snapshot
        )
        location = evaluate(snapshot, args.leb_checkout, args.output_root, args.timeout)
        metrics = load_evaluation(location).metrics
    except (OSError, ValueError) as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"Calculator reference results for Last Epoch 1.4.7: health {metrics['health']['value']} health points; armour {metrics['armour']['value']} armour rating"
    )
    print(f"Saved evaluation: {location}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
