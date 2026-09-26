"""Resolve the shared root for generated local artifacts."""

import os
from pathlib import Path


def resolve_artifact_root(root: Path | None = None) -> Path:
    """Use an explicit root, the environment, or the current directory default."""
    if root is not None:
        return root.expanduser()
    configured = os.environ.get("ARPG_BUILD_LAB_ARTIFACTS_ROOT")
    return Path(configured).expanduser() if configured else Path("artifacts")
