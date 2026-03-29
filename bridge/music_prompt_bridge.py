#!/usr/bin/env python3
"""
Deterministic brief → music-generation prompt (text only).

Input: get_brief() / bridge output (JSON with a `brief` object, or the bare brief).
Output: one structured object for an external music model—no API calls, no audio.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def build_music_prompt(brief: dict[str, Any]) -> dict[str, Any]:
    """Turn brief contract v1 into a single generator prompt + constraints."""
    required = ("composer_id", "intent", "musical_direction")
    for k in required:
        if k not in brief:
            raise ValueError(f"brief missing required key: {k!r}")

    md = brief["musical_direction"]
    if not isinstance(md, dict):
        raise ValueError("musical_direction must be an object")

    aims = md.get("aims") or []
    style = md.get("style_elements") or []
    habits = md.get("process_habits") or []
    seed = brief.get("seed") or {}

    intent = str(brief["intent"]).strip()
    cid = str(brief["composer_id"])

    clauses: list[str] = [
        f"Compose a work reflecting this creative brief for composer id {cid}: {intent}."
    ]
    if style:
        clauses.append(
            "Favor sonic characteristics such as " + ", ".join(str(s) for s in style) + "."
        )
    if aims:
        clauses.append(
            "Honor artistic aims including " + "; ".join(str(a) for a in aims) + "."
        )
    if habits:
        clauses.append(
            "Let process hints inform shape: " + "; ".join(str(h) for h in habits) + "."
        )
    if seed and isinstance(seed, dict):
        bits = [
            f"{k}={v}"
            for k, v in sorted(seed.items())
            if k != "index" and v is not None and str(v).strip()
        ]
        if bits:
            clauses.append("Seed row context: " + "; ".join(bits) + ".")

    generator_prompt = " ".join(clauses)

    constraints = [
        "Stay within the vocabulary and priorities implied by the brief; do not invent historical facts.",
        "Prefer intimate, exacting musical craft over melodrama or caricature.",
        "Favor nuanced pacing and phrasing over forced climax unless the brief clearly demands it.",
    ]

    return {
        "composer_id": cid,
        "intent": intent,
        "generator_prompt": generator_prompt,
        "constraints": constraints,
        "output_target": "external_music_model_prompt",
    }


def _parse_payload(raw: dict[str, Any]) -> dict[str, Any]:
    if "brief" in raw and isinstance(raw["brief"], dict):
        return raw["brief"]
    return raw


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Convert composer brief JSON into a music-model prompt object.",
    )
    ap.add_argument(
        "--file",
        type=Path,
        help="JSON file (bridge output or bare brief). Default: read stdin",
    )
    args = ap.parse_args()

    if args.file:
        text = args.file.read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()
    raw = json.loads(text)
    if not isinstance(raw, dict):
        raise SystemExit("JSON root must be an object")
    brief = _parse_payload(raw)
    out = build_music_prompt(brief)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
