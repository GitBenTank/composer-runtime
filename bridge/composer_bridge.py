#!/usr/bin/env python3
"""Deterministic JSON bridge: profile → summary, concepts, brief, reflection. No agent or domain logic."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_RUNTIME_ROOT = Path(__file__).resolve().parent.parent


def _ensure_composer_system_path() -> None:
    """Prefer sibling ../composer-system; no pip install required for local dev."""
    for candidate in (
        _RUNTIME_ROOT.parent / "composer-system",
        _RUNTIME_ROOT / "vendor" / "composer-system",
    ):
        pkg = candidate / "composer_system"
        if pkg.is_dir():
            root = str(candidate.resolve())
            if root not in sys.path:
                sys.path.insert(0, root)
            return
    try:
        import composer_system  # noqa: F401
    except ImportError as e:
        raise SystemExit(
            "composer_system not found. Clone composer-system next to composer-runtime, or: "
            "pip install -e ../composer-system"
        ) from e


_ensure_composer_system_path()

from composer_system.brief import get_brief  # noqa: E402
from composer_system.creation import creative_concepts  # noqa: E402
from composer_system.exceptions import ProfileLoadError  # noqa: E402
from composer_system.load import load_profile  # noqa: E402
from composer_system.reflection import (  # noqa: E402
    human_reflection_summary,
    structured_reflection,
)


def resolve_data_dir(arg: str) -> Path:
    """Expand, resolve, and validate ``--data-dir`` for bridge CLIs."""
    p = Path(arg).expanduser()
    try:
        p = p.resolve(strict=False)
    except OSError as e:
        raise SystemExit(f"Cannot resolve --data-dir {arg!r}: {e}") from e
    if not p.is_dir():
        raise SystemExit(f"--data-dir is not a directory: {p}")
    return p


def main() -> None:
    ap = argparse.ArgumentParser(description="Emit summary, concepts, brief JSON for OpenClaw.")
    ap.add_argument("composer_id")
    ap.add_argument(
        "--intent",
        required=True,
        help='User intent, e.g. nocturne about distance and memory',
    )
    ap.add_argument(
        "--data-dir",
        default=str(_RUNTIME_ROOT / "data" / "composers"),
        help="Directory containing <id>.json profiles",
    )
    args = ap.parse_args()

    data_dir = resolve_data_dir(args.data_dir)
    try:
        profile = load_profile(args.composer_id, data_dir=data_dir)
    except ProfileLoadError as e:
        raise SystemExit(str(e)) from e

    payload = {
        "composer": {"id": profile.id, "display_name": profile.display_name},
        "summary": human_reflection_summary(profile),
        "concepts": creative_concepts(profile),
        "brief": get_brief(profile, args.intent),
        "reflection_struct": structured_reflection(profile),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
