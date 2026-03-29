---
name: composer
description: "Load a historically grounded composer profile and emit summary, concept seeds, and a structured creative brief (no audio generation)."
version: "1.0"
---

# Composer Skill

## Purpose

This skill turns a user request into a **structured composer brief** using local profiles and deterministic transforms.

## Boundaries (non-negotiable)

- Do NOT generate audio, MIDI, or publish anything.
- Do NOT invent historical claims beyond the profile fields.
- Do NOT run arbitrary shell commands.
- Only call the bridge script `bridge/composer_bridge.py` with a composer id and intent.
- Composer IDs must be one of: `bach`, `beethoven`, `chopin`, `mozart` (expand only when profiles exist).

## Inputs

User will request in one of these forms:

- `/composer <id> summary`
- `/composer <id> concepts`
- `/composer <id> brief "<intent text>"`
- or conversational equivalents.

## Procedure

1. Parse:
   - `composer_id` (must match an existing JSON file under `data/composers/<id>.json`)
   - `intent` (required for brief; optional for summary/concepts)
2. Call the bridge script (from workspace root):

   `python bridge/composer_bridge.py <composer_id> --intent "<intent>" --data-dir data/composers`

3. Return only the relevant parts:
   - For `summary`: return `summary`
   - For `concepts`: return `concepts.concept_seeds`
   - For `brief`: return `brief` plus `summary` for context

## Output formats

### Summary output

Return:

- display name + id
- the `summary` paragraph

### Concepts output

Return numbered list of concept seeds (key="value" pairs)

### Brief output

Return a JSON object with:

- composer_id
- intent
- musical_direction (aims/style_elements/process_habits)
- seed
- output_target

## Error handling

- If composer_id not found: list allowed ids.
- If intent is missing for `brief`: ask for one sentence intent.
