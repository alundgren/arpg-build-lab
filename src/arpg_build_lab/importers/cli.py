"""Command for one requested planner build or saved response."""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from arpg_build_lab.domain.snapshot import BuildSnapshot
from arpg_build_lab.importers.letools import (
    ImportError,
    fetch,
    parse_build,
    verify_saved_versions,
)


def _invalid_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON number: {value}")


def save(
    raw: bytes,
    snapshot: BuildSnapshot,
    root: Path = Path("artifacts"),
    *,
    input_path: Path | None = None,
) -> Path:
    bucket = (
        snapshot.game_version
        if snapshot.game_version
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*", snapshot.game_version)
        else "unknown"
    )
    run = f"letools-{snapshot.source_id}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
    location = root / bucket / "imports" / run
    location.mkdir(parents=True, exist_ok=False)
    (location / "raw.json").write_bytes(raw)
    (location / "snapshot.json").write_text(
        json.dumps(snapshot.to_dict(), indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    provenance = {
        "imported_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_kind": "saved_response" if input_path else "direct_request",
        "input_path": str(input_path) if input_path else None,
        "source_url": snapshot.source_url,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "schema_version": snapshot.schema_version,
        "game_version": snapshot.game_version,
        "importer_version": snapshot.importer_version,
        "lookup_revision": snapshot.lookup_revision,
    }
    (location / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n"
    )
    return location


def load(location: Path) -> BuildSnapshot:
    path = location / "snapshot.json"
    snapshot = BuildSnapshot.from_dict(
        json.loads(path.read_text(), parse_constant=_invalid_constant)
    )
    raw_path = Path(snapshot.raw_path)
    if raw_path.is_absolute() or ".." in raw_path.parts:
        raise ValueError("Snapshot raw_path must stay within its run directory")
    raw = (location / raw_path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != snapshot.raw_sha256:
        raise ValueError("Snapshot raw response hash does not match")
    verify_saved_versions(snapshot, raw)
    provenance_path = location / "provenance.json"
    if provenance_path.exists():
        provenance = json.loads(
            provenance_path.read_text(), parse_constant=_invalid_constant
        )
        if not isinstance(provenance, dict):
            raise ValueError("Import provenance must be an object")
        for key, expected in {
            "source_url": snapshot.source_url,
            "raw_sha256": snapshot.raw_sha256,
            "schema_version": snapshot.schema_version,
            "game_version": snapshot.game_version,
            "importer_version": snapshot.importer_version,
            "lookup_revision": snapshot.lookup_revision,
        }.items():
            if provenance.get(key) != expected:
                raise ValueError(f"Import provenance {key} does not match snapshot")
    return snapshot


def summary(snapshot: BuildSnapshot, location: Path) -> str:
    passive_points = sum(snapshot.passives["selected"].values())
    lines = [
        f"Game version: {snapshot.game_version or 'unknown'}",
        f"Class/mastery: {snapshot.character['class_id']}/{snapshot.character['mastery_id']}; level: {snapshot.character['level']}",
        f"Passives: {len(snapshot.passives['selected'])} nodes, {passive_points} points",
        f"Skills: {len(snapshot.skills)} trees; "
        + ", ".join(
            f"{s['source_tree_id']} (slot {s['slot_number']}, level {s['level']})"
            for s in snapshot.skills
        ),
        f"Equipment: {len(snapshot.equipment)} slots; idols: {len(snapshot.idols)}; blessings: {len(snapshot.blessings)}",
        "Equipment IDs: "
        + ", ".join(
            f"{slot}={item['source_id']}" for slot, item in snapshot.equipment.items()
        ),
        "Idol positions: "
        + ", ".join(
            f"({item['x']},{item['y']})={item['source_id']}" for item in snapshot.idols
        ),
        "Blessing IDs: "
        + ", ".join(
            f"{slot}={item['source_id']}" for slot, item in snapshot.blessings.items()
        ),
        f"Unresolved LETools item IDs: {', '.join(snapshot.unresolved['item_ids']) or 'none'}",
        f"Unresolved LETools affix IDs: {', '.join(snapshot.unresolved['affix_ids']) or 'none'}",
        f"Unresolved LETools blessing IDs: {', '.join(snapshot.unresolved['blessing_ids']) or 'none'}",
        f"Unsupported source sections in raw response: {', '.join(snapshot.unsupported_sections) or 'none'}",
        f"Raw: {location / 'raw.json'}",
        f"Snapshot: {location / 'snapshot.json'}",
        f"Provenance: {location / 'provenance.json'}",
    ]
    if snapshot.game_version is None:
        lines.insert(1, f"Version evidence: {snapshot.version_evidence}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Save one LETools planner build")
    parser.add_argument("url", help="Explicit HTTPS LETools planner URL")
    parser.add_argument(
        "--raw-file", type=Path, help="Import an existing raw JSON response offline"
    )
    parser.add_argument("--output-root", type=Path, default=Path("artifacts"))
    args = parser.parse_args(argv)
    try:
        raw = args.raw_file.read_bytes() if args.raw_file else fetch(args.url)
        snapshot = parse_build(raw, args.url)
        location = save(raw, snapshot, args.output_root, input_path=args.raw_file)
    except (ImportError, OSError, ValueError) as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1
    print(summary(snapshot, location))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
