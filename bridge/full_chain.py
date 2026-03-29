#!/usr/bin/env python3
"""One-shot: composer profile (summary, concepts, brief) → music_prompt via existing bridges."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import composer_bridge  # noqa: F401  # side effect: composer_system on sys.path
from composer_bridge import (
    ProfileLoadError,
    creative_concepts,
    get_brief,
    human_reflection_summary,
    load_profile,
    resolve_data_dir,
)
from music_prompt_bridge import build_music_prompt

_RUNTIME_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Emit composer + summary + concepts + brief + music_prompt as one JSON object.",
    )
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

    brief = get_brief(profile, args.intent)
    try:
        music_prompt = build_music_prompt(brief)
    except ValueError as e:
        raise SystemExit(str(e)) from e

    out = {
        "composer": {"id": profile.id, "display_name": profile.display_name},
        "summary": human_reflection_summary(profile),
        "concepts": creative_concepts(profile),
        "brief": brief,
        "music_prompt": music_prompt,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
