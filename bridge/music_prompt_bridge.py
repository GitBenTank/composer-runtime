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

_BASE_CONSTRAINTS = [
    "Derive every musical decision from the brief's aims, style targets, process habits, seed row, and (only secondarily) the user orientation; do not invent biography, dates, or historical specifics absent from those strings.",
    "Spell out concrete scoring means: register, doubling, phrase length, metric frame, articulation, voice-leading density, repetition vs. permutation—avoid broad aesthetic labels and vague hype.",
]

_DEFAULT_EXTRA_CONSTRAINTS = [
    "Let process habits shape how material returns, shortens, recombines, or is rescored across sections, not merely surface colour.",
    "Where the seed row names creative temperament, translate it into timing, voicing emphasis, and motivic treatment—not programme narration.",
]

_COMPOSER_CONSTRAINTS: dict[str, list[str]] = {
    "bach": [
        "Prioritize linear clarity and harmonic function in counterpoint; let chorale or cantus-derived logic govern phrase goals where relevant.",
        "Favor disciplined voice-leading and rhythmic motor over explosive tutti gestures unless aims explicitly ask for broader rhetoric.",
    ],
    "beethoven": [
        "Let developmental drama and motivic narrative drive form; metric stress and registral spacing should clarify rhetorical intent.",
        "Treat cyclical or integrative aims as structural glue—returns and transformations should be traceable in the score, not only implied.",
    ],
    "chopin": [
        "Treat rubato and ornamental variation as structural parameters, not only surface decoration; phrase ends and repeats are opportunities for directed remaking.",
        "Dance genres may carry large-scale tension; keep bass–melody dialogue and pianistic voicing explicit in specification.",
    ],
    "mozart": [
        "Balance singing, periodic lyricism with ensemble continuity; inner voices and orchestral colour should clarify character without muddying the line.",
        "Where theatrical or vocal aims surface, differentiate strata (melody, harmony, rhythm) instead of homogenizing texture.",
    ],
    "haydn": [
        "Carry wit through phrase rhythm, conversational orchestration, and timing of cadential surprises; prefer clarified dialogue over continuous saturated wash.",
        "Treat small motivic cells as plastic: develop through reorder, fragment, extension, and surprise closure rather than through unbroken lyric span alone.",
    ],
}


def _seed_focus_parts(seed: dict[str, Any]) -> str | None:
    """Compact seed line: seed_id (or seed_index) + single focus string—no repeat of full row."""
    if not seed:
        return None
    bits: list[str] = []
    sid = seed.get("seed_id")
    if sid is not None and str(sid).strip():
        bits.append(f"seed_id={str(sid).strip()}")
    elif seed.get("index") is not None:
        bits.append(f"seed_index={seed['index']}")
    focus: str | None = None
    for key in ("musical_element", "artistic_aim"):
        v = seed.get(key)
        if v is not None and str(v).strip():
            focus = str(v).strip()
            break
    if not focus:
        summ = seed.get("summary")
        if summ is not None and str(summ).strip():
            focus = str(summ).split("·")[0].strip()
    if focus:
        bits.append(f"focus={focus}")
    return "; ".join(bits) if bits else None


def _build_generator_prompt(
    cid: str,
    musical_direction: dict[str, Any],
    seed: dict[str, Any],
    intent: str,
) -> str:
    """Reference structured state instead of restating aims/style/habits in prose."""
    md_json = json.dumps(musical_direction, ensure_ascii=False, separators=(",", ":"))
    parts: list[str] = [
        f"Composer profile identifier: {cid}. Lock scoring priorities to the governing brief below; "
        "they override any colloquial reading of the user request.",
        "Musical direction (authoritative, do not reinterpret):\n"
        + md_json
        + ".",
    ]
    seed_line = _seed_focus_parts(seed)
    if seed_line:
        parts.append(
            "Primary seed focus (keep audible as a thread through sections, not as a one-off gesture): "
            + seed_line
            + "."
        )
    if intent:
        parts.append(
            "User orientation (interpret this request strictly through the profile above; "
            "adapt its terms rather than replacing them): "
            + intent
            + "."
        )
    return " ".join(parts)


def build_music_prompt(brief: dict[str, Any]) -> dict[str, Any]:
    """Turn brief contract v1 into a single generator prompt + constraints."""
    required = ("composer_id", "musical_direction")
    for k in required:
        if k not in brief:
            raise ValueError(f"brief missing required key: {k!r}")
    if "trimmed_intent" not in brief and "intent" not in brief:
        raise ValueError("brief missing required key: 'trimmed_intent' (or legacy 'intent')")

    md = brief["musical_direction"]
    if not isinstance(md, dict):
        raise ValueError("musical_direction must be an object")

    raw_seed = brief.get("seed") or {}
    seed = raw_seed if isinstance(raw_seed, dict) else {}

    raw_intent = brief.get("trimmed_intent", brief.get("intent", ""))
    intent = str(raw_intent).strip()
    cid = str(brief["composer_id"])

    generator_prompt = _build_generator_prompt(cid, md, seed, intent)

    extra = _COMPOSER_CONSTRAINTS.get(cid, _DEFAULT_EXTRA_CONSTRAINTS)
    constraints = list(_BASE_CONSTRAINTS) + list(extra)

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
