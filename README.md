# composer-runtime

OpenClaw-oriented **workspace** for composer tooling. It does **not** replace [composer-system](https://github.com/GitBenTank/composer-system): that repo stays the **data + deterministic transforms** source of truth. This repo holds the **bridge**, **local profile copies**, and **OpenClaw skill** playbooks.

## Layout

- `bridge/composer_bridge.py` — JSON CLI for summary, concepts, brief (+ optional full reflection for debugging).
- `bridge/music_prompt_bridge.py` — brief JSON → single **text** music-model prompt + constraints (no APIs, no audio).
- `data/composers/` — read-only copy of profiles (sync from composer-system when profiles change).
- `skills/composer/SKILL.md` — OpenClaw skill contract.
- `outputs/` — optional local artifacts.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Option A — sibling clone (no pip install):** put `composer-system` next to this folder:

```text
parent/
  composer-system/    # has composer_system package
  composer-runtime/    # this repo
```

The bridge adds `../composer-system` to `PYTHONPATH` automatically.

**Option B — editable install:**

```bash
pip install -e ../composer-system
```

**Option C — from GitHub:**

```bash
pip install "git+https://github.com/GitBenTank/composer-system.git"
```

Refresh profile data when needed:

```bash
cp -R ../composer-system/data/composers data/
```

## Milestone 1 — test the bridge

```bash
python bridge/composer_bridge.py chopin --intent "nocturne about distance and memory" --data-dir data/composers
```

Expect JSON with `summary`, `concepts`, `brief`, and `reflection_struct`.

## Milestone 2 — music prompt (still no audio)

Pipe full bridge JSON into the prompt bridge (stdin):

```bash
python bridge/composer_bridge.py chopin --intent "nocturne about distance and memory" --data-dir data/composers \
  | python bridge/music_prompt_bridge.py
```

Or pass a saved JSON file:

```bash
python bridge/composer_bridge.py chopin --intent "nocturne about distance and memory" --data-dir data/composers > /tmp/out.json
python bridge/music_prompt_bridge.py --file /tmp/out.json
```

Output: `generator_prompt`, `constraints`, `output_target: external_music_model_prompt`.

## OpenClaw

Point OpenClaw at this directory as the workspace. Skills live under `skills/`.

```bash
openclaw skills list
openclaw skills info composer
openclaw skills check
```

Use the **composer** skill playbook; it documents calling `bridge/composer_bridge.py` only, with narrow scope (no audio, no invented history). If the agent does not run the bridge, execute that command manually from the workspace root, then tighten tool policy to allow **only** that script path.

### Chat smoke tests

1. `Use the composer skill to get a summary for chopin.`
2. `Use the composer skill to get concept seeds for bach.`
3. `Use the composer skill to create a brief for chopin with the intent: nocturne about distance and memory.`

### If skills do not appear

From workspace root, capture:

```bash
pwd
find skills -maxdepth 2 -type f
cat skills/composer/SKILL.md
openclaw skills list
openclaw skills info composer
openclaw skills check
```
