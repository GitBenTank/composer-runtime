# composer-runtime

**Execution layer** for [composer-system](https://github.com/GitBenTank/composer-system): bridges turn composer profiles plus user intent into **structured text** for downstream music models. No audio, no external APIs in the bridges.

## What this does

Given a composer profile (Bach, Haydn, Chopin, …) and a short **intent** (“playful symphony”, “nocturne about distance and memory”), this repo produces **deterministic JSON**: human-facing summary and concepts, a **brief**, and a **music_prompt** (`generator_prompt` + `constraints`) that stay faithful to the profile. The user line is **secondary**; profile fields drive interpretation. The runtime **references structured state** (e.g. `musical_direction` as JSON) instead of repeating the same instructions in prose.

## Pipeline

```text
composer-system    get_brief(profile, intent)
       │
       ▼
composer-runtime   build_music_prompt(brief)   (+ optional composer_bridge-only steps)
       │
       ▼
music model        (Suno, MusicGen, your stack—out of band)
```

One-shot handoff: **`bridge/full_chain.py`** loads the profile, builds the brief, then builds `music_prompt` in the same process.

## Example (same intent, different composers)

**Intent:** `playful symphony`

| Composer   | What changes in `music_prompt.constraints` (composer-specific tail) |
|-----------|----------------------------------------------------------------------|
| **Haydn** | Cadential **surprises**, **conversational** orchestration, **motivic cells** plasticity (fragment, extension, surprise closure). |
| **Beethoven** | **Developmental drama** and **motivic narrative**; metric stress and registral spacing; cyclical **returns** traceable in the score. |

Run the command below and diff the full JSON: same intent string, different profile → different `generator_prompt` and constraints.

## How to run

From repo root (with [composer-system](https://github.com/GitBenTank/composer-system) available—sibling clone or `pip install -e ../composer-system`):

```bash
python3 bridge/full_chain.py haydn --intent "playful symphony" --data-dir data/composers
```

Top-level JSON keys: `composer`, `summary`, `concepts`, `brief`, `music_prompt`.

Other CLIs:

- `python3 bridge/composer_bridge.py <id> --intent "…" --data-dir data/composers` — summary, concepts, brief (+ `reflection_struct`).
- Pipe that stdout into `python3 bridge/music_prompt_bridge.py` if you want prompt-only from full bridge JSON.

## Layout

| Path | Role |
|------|------|
| `bridge/full_chain.py` | Profile → summary, concepts, brief, **music_prompt** (single JSON). |
| `bridge/composer_bridge.py` | Profile → summary, concepts, brief (+ reflection). |
| `bridge/music_prompt_bridge.py` | Brief → `generator_prompt`, `constraints`. |
| `data/composers/` | Profile JSON copies; refresh from composer-system when needed. |
| `skills/composer/SKILL.md` | OpenClaw skill contract (prefers `full_chain` when appropriate). |
| `tests/` | Regression tests; `pytest` in CI. |

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ../composer-system   # or keep composer-system as ../composer-system for PYTHONPATH
pip install -r requirements.txt    # pytest, etc.
```

Sibling layout (recommended for development):

```text
parent/
  composer-system/
  composer-runtime/    # this repo
```

Refresh profiles when upstream data changes:

```bash
cp -R ../composer-system/data/composers data/
```

## Tests & CI

```bash
python3 -m pytest tests/ -q
```

GitHub Actions checks out **composer-runtime** and **composer-system** side by side, installs composer-system editable, installs `requirements.txt`, runs `python3 -m pytest tests/ -q`.

## OpenClaw

Point the agent workspace at this repo (or mount `skills/` via `extraDirs`). Use the **composer** skill: it routes to `python3 bridge/...` with narrow tool scope. See `skills/composer/SKILL.md` and [OpenClaw skills docs](https://docs.openclaw.ai/tools/skills).
