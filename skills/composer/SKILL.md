---
name: composer
description: "Load a historically grounded composer profile; emit summary, concept seeds, structured brief, optional music-model prompt, or a one-shot full_chain JSON (no audio generation)."
version: "1.0"
---

# Composer Skill

## Purpose

This skill MUST route composer requests through **deterministic bridges only**:

- `bridge/full_chain.py` — **preferred** when the user wants **composer, summary, concepts, brief, and music_prompt** in a **single** JSON (one command, minimal shell surface).
- `bridge/composer_bridge.py` — profile → summary, concepts, brief (+ optional `reflection_struct` in stdout).
- `bridge/music_prompt_bridge.py` — **only after** valid `composer_bridge.py` JSON (or bare brief), to turn `brief` into `generator_prompt` + `constraints`.

Outputs MUST come from those scripts—not from paraphrase, invention, or ad hoc prompting.

## Boundaries (non-negotiable)

- DO NOT generate audio, MIDI, or published artifacts.
- DO NOT invent or extend historical claims beyond what the profile JSON supports.
- DO NOT use `python`; you MUST use `python3`.
- DO NOT run shell commands except these **approved** forms (workspace root, no other programs, no subshell tricks):
  1. **Full chain (preferred for end-to-end handoff):**  
     `python3 bridge/full_chain.py <composer_id> --intent "<intent>" [--data-dir data/composers]`
  2. **Composer only:**  
     `python3 bridge/composer_bridge.py <composer_id> --intent "<intent>" --data-dir data/composers`
  3. **Music prompt (composer + music prompt, two processes):**  
     `python3 bridge/composer_bridge.py <composer_id> --intent "<intent>" --data-dir data/composers | python3 bridge/music_prompt_bridge.py`
  4. **Music prompt (two steps, if you cannot use a pipe):** run form (2); then run `python3 bridge/music_prompt_bridge.py` with **stdin** set to the **exact** stdout string from form (2)—byte-for-byte the same JSON object, unmodified.
- When **full_chain** satisfies the user request, you MUST use form (1) **only**—DO NOT also run `composer_bridge.py` and `music_prompt_bridge.py` in parallel for the same intent.
- DO NOT pass a hand-edited, partial, or re-serialized “brief only” blob into `music_prompt_bridge.py` unless it is **identical** to the `brief` object inside the composer bridge JSON you just received (prefer stdin = **full** composer bridge stdout so the script extracts `brief` itself).
- DO NOT substitute reading `data/composers/*.json` for calling an approved bridge when the user asked for scripted output; bridge stdout is authoritative for profile-derived fields.
- Composer IDs MUST match a filename stem under `data/composers/*.json` (e.g. `bach`, `beethoven`, `chopin`, `haydn`, `mozart`).

## Inputs

The user MAY phrase requests as:

- `/composer <id> summary`
- `/composer <id> concepts`
- `/composer <id> brief "<intent text>"`
- `/composer <id> music-prompt "<intent text>"` (or conversational: music prompt, generator prompt, external music model prompt, `music_prompt_bridge`, etc.)
- **Full chain:** “full chain”, “full pipeline”, “composer + brief + music prompt”, “everything in one JSON”, `full_chain.py`, **or** natural phrasing such as “generate a Chopin music prompt for …”, “music prompt for a nocturne about …”, or any request that clearly needs **composer, summary, concepts, brief, and music_prompt** together—**including when the user never says the words “full chain.”**

You MUST map conversational equivalents to the same actions and bridge rules.

## Procedure

1. You MUST parse `composer_id` (MUST match `data/composers/<id>.json`).
2. You MUST set `--intent` where the bridge CLI requires it:
   - For **brief**, **music prompt**, or **full chain**: you MUST use the user’s exact intent string (ask for it if missing; DO NOT run the bridge until you have it).
   - For **summary** or **concepts** only: if the user gave no intent, you MUST pass `--intent "profile inquiry"` solely to satisfy the CLI. You MUST NOT include or emphasize `brief`, `music_prompt`, or `reflection_struct` in the user-visible reply for those actions.
3. You MUST run bridges per **Boundaries**:
   - **Full chain:** form (1), once.
   - **Summary, concepts, or brief:** form (2), once (unless full chain was chosen).
   - **Music prompt (without full_chain):** form (3) **or** sequence (4); you MUST NOT run `music_prompt_bridge.py` without first obtaining successful composer bridge JSON for the same `composer_id` and `intent`.
4. You MUST parse stdout as JSON. You MUST NOT fabricate fields. If a bridge errors, you MUST surface the error; DO NOT invent fallback content.
5. When `music_prompt_bridge.py` runs (forms 3–4), you MUST parse its stdout JSON. You MUST NOT fabricate `generator_prompt` or `constraints`.

For each action, you MUST return only what **Output requirements** allow—except for **brief**, where you MUST include every section under **Brief action**; except for **music prompt**, where you MUST include every section under **Brief action** and every field under **Music prompt action**; except for **full chain**, where you MUST follow **Full chain action**.

## Output requirements (strict)

**Rendering is not summarization:** you MUST present bridge output as **transcription**, not as an editorial rewrite.

You MUST NOT replace bridge text with your own summary, abridgment, or “cleaner” JSON. Prose MAY only introduce section labels (e.g. `**Summary**`); every fact string MUST be copied from the bridge output. You MUST NOT substitute `reflection_struct`, workspace docs, or model-invented prose for the `summary` field.

### Summary action

You MUST return:

1. **Composer** — `display_name` and `id` from `composer` (format: `{display_name} ({id})`).
2. **Summary** — the `summary` string **in full**, verbatim from the bridge.

### Concepts action

You MUST return:

1. **Composer** — `display_name` and `id` from `composer`.
2. **Concept seeds** — **every** object in `concepts.concept_seeds`, in order, numbered `1.`, `2.`, ….
3. For each seed, you MUST list **all** key-value pairs present in that object (e.g. `index`, `musical_element`, `process_habit`, `artistic_aim`, `personality_trait`). If a key is absent in JSON, skip that key—DO NOT invent keys or values.

### Brief action

You MUST return **all four** sections below, in this order. DO NOT omit sections. DO NOT substitute abbreviated summary or partial seeds.

1. **Composer** — `display_name` and `id` from top-level `composer`.
2. **Summary** — the full `summary` string verbatim from the bridge (entire paragraph, unchanged).
3. **Concept seeds** — **all** entries in `concepts.concept_seeds`, numbered, with **all** fields per seed as in the Concepts action rules.
4. **Brief JSON** — the value of the `brief` key **only**, as JSON, **unmodified**: same structure, strings, and scalars as in bridge output. You MUST put it in a fenced code block with the `json` language tag, containing exactly the serialized `brief` object (pretty-print or one line is acceptable if it round-trips to the same object).

After presenting these four sections, you MUST NOT add alternative briefs, “improved” copy, or duplicate JSON that disagrees with the bridge.

### Music prompt action

This action applies when the user requests a music / generator prompt derived from the brief **without** using **full_chain**.

You MUST run **Music prompt** procedure (pipeline or two-step) so `music_prompt_bridge.py` receives the full composer bridge JSON on stdin.

You MUST return:

1. **All four sections** listed under **Brief action**—same order, same verbatim rules—using the composer bridge JSON from that same run. DO NOT skip Composer, Summary, Concept seeds, or Brief JSON.
2. **Generator prompt** — the `generator_prompt` string from `music_prompt_bridge.py` stdout, **in full**, verbatim.
3. **Constraints** — **every** string in the `constraints` array from `music_prompt_bridge.py` stdout, in order, numbered `1.`, `2.`, … (or an equivalent bullet list). DO NOT omit, merge, or rewrite items.

You MUST NOT add a second invented `generator_prompt`, DO NOT paste only an excerpt of `constraints`, and DO NOT claim the music prompt ran without showing these two fields.

### Full chain action

Use when the user’s goal matches **Boundaries** form (1).

You MUST run:

`python3 bridge/full_chain.py <composer_id> --intent "<intent>" [--data-dir data/composers]`

You MUST parse the single stdout JSON object. Its top-level keys are: `composer`, `summary`, `concepts`, `brief`, `music_prompt`.

You MUST return:

1. **Composer** — same content as top-level `composer` (`display_name` and `id`), verbatim.
2. **Summary** — the `summary` string **in full**, verbatim.
3. **Concept seeds** — **all** objects in `concepts.concept_seeds` under top-level `concepts`, numbered, with **all** fields per seed as in **Concepts action** (verbatim from that structure).
4. **Brief JSON** — top-level `brief` only, **unmodified**, in a fenced `json` code block (same rule as **Brief action** §4).
5. **Music prompt** — from top-level `music_prompt`, verbatim:
   - `composer_id`, `intent`, `output_target` (if present),
   - **generator_prompt** in full,
   - **constraints** — every string, in order, numbered or bulleted.

DO NOT omit `music_prompt` subfields. DO NOT substitute composer-only or brief-only output when the user asked for the full chain.

**Full chain — anti-compression (strict):** After running `full_chain.py`, the **Summary** section MUST be **only** the top-level `summary` string character-for-character (same Unicode text as in the JSON value). DO NOT prepend labels like “Working assumptions”, DO NOT blend in `reflection_struct` or `concepts.narrative_hooks`, and DO NOT reshape into bullets unless the `summary` string itself already contains that layout. For **Concept seeds**, emit **every** key and value present on each object in `concepts.concept_seeds` (e.g. `seed_id`, `dimensions`, `summary` when present)—DO NOT normalize down to a shortened template.

## Error handling

- If `composer_id` is missing or not in the allowed set: you MUST list allowed IDs from `data/composers/` (filename stems).
- If the user requests **brief**, **music prompt**, or **full chain** without an intent: you MUST ask for a one-sentence intent and DO NOT run the bridge until you have it.
- If `python3` or any bridge fails (including **ProfileLoadError** / invalid brief for `build_music_prompt`): you MUST report the error text; DO NOT hallucinate bridge output.
