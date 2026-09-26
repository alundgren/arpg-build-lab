import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    run = ["uv", "run", "--no-sync"]
    checks = [
        ("environment", ["uv", "sync", "--locked"]),
        ("lint", [*run, "ruff", "check", "."]),
        ("format", [*run, "ruff", "format", "--check", "--diff", "."]),
        (
            "complexity",
            [
                *run,
                "ruff",
                "check",
                "--select",
                "C901,PLR0912,PLR0915",
                "--exit-zero",
                "--quiet",
                "--output-format",
                "concise",
                ".",
            ],
        ),
        (
            "tests",
            [
                *run,
                "python",
                "-m",
                "unittest",
                "discover",
                "-s",
                "src/arpg_build_lab/importers/tests",
                "--buffer",
            ],
        ),
        (
            "evaluator tests",
            [
                *run,
                "python",
                "-m",
                "unittest",
                "discover",
                "-s",
                "src/arpg_build_lab/evaluators/tests",
                "--buffer",
                "-p",
                "test_evaluation.py",
            ],
        ),
        (
            "dataset tests",
            [
                *run,
                "python",
                "-m",
                "unittest",
                "discover",
                "-s",
                "src/arpg_build_lab/datasets/tests",
                "--buffer",
            ],
        ),
        ("build", ["uv", "build"]),
    ]
    for name, command in checks:
        try:
            result = subprocess.run(
                command,
                cwd=root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
            )
        except OSError as exc:
            print(f"FAIL: {name}: {exc}", file=sys.stderr)
            return 1
        if result.returncode:
            print(f"FAIL: {name} (exit {result.returncode})", file=sys.stderr)
            print(result.stdout.rstrip(), file=sys.stderr)
            return result.returncode
        if name == "complexity" and result.stdout.strip():
            print("Complexity advisories:")
            print(result.stdout.rstrip())
    print("OK: lint, format, tests, build")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
