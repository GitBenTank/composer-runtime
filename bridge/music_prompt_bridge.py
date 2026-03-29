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

_SEED_DISPLAY_KEYS = (
    "seed_id",
    "summary",
    "artistic_aim",
    "musical_element",
    "personality_trait",
    "process_habit",
)

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


def _format_seed_block(seed: dict[str, Any]) -> str:
    parts: list[str] = []
    for k in _SEED_DISPLAY_KEYS:
        v = seed.get(k)
        if v is None or str(v).strip() == "":
            continue
        if k == "summary":
            parts.append(f"summary={v}")
        elif k == "seed_id":
            parts.append(f"seed_id={v}")
        else:
            parts.append(f"{k}={v}")
    dim = seed.get("dimensions")
    if isinstance(dim, list) and dim:
        parts.append("dimensions=" + ",".join(str(d) for d in dim))
    return "; ".join(parts)


def _generator_blocks(
    cid: str,
    seed: dict[str, Any],
    aims: list[str],
    style: list[str],
    habits: list[str],
    intent: str,
) -> list[str]:
    blocks: list[str] = [
        f"Composer profile identifier: {cid}. Lock scoring priorities to the profile-derived fields below; "
        "they override any colloquial reading of the user request."
    ]
    seed_text = _format_seed_block(seed)
    if seed_text:
        blocks.append(
            "Primary concept seed (keep this combination audible as a thread through sections, not as a one-off gesture): "
            + seed_text
            + "."
        )
    if aims:
        blocks.append(
            "Compositional aims—realize as voice-leading, formal pacing, and registral goals, not as programme labels: "
            + " | ".join(aims)
            + "."
        )
    if style:
        blocks.append(
            "Sonic and formal targets—name them when specifying instruments, voicings, phrase groups, and motivic work: "
            + " | ".join(style)
            + "."
        )
    if habits:
        blocks.append(
            "Process habits—translate into how material is drafted, varied, rescored, or repurposed across the piece: "
            + "; ".join(habits)
            + "."
        )
    if intent:
        blocks.append(
            "User orientation (interpret this request strictly through the profile above; "
            "adapt its terms rather than replacing them): "
            + intent
            + "."
        )
    return blocks


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

    aims = [str(a).strip() for a in (md.get("aims") or []) if str(a).strip()]
    style = [str(s).strip() for s in (md.get("style_elements") or []) if str(s).strip()]
    habits = [str(h).strip() for h in (md.get("process_habits") or []) if str(h).strip()]
    raw_seed = brief.get("seed") or {}
    seed = raw_seed if isinstance(raw_seed, dict) else {}

    raw_intent = brief.get("trimmed_intent", brief.get("intent", ""))
    intent = str(raw_intent).strip()
    cid = str(brief["composer_id"])

    generator_prompt = " ".join(_generator_blocks(cid, seed, aims, style, habits, intent))

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
