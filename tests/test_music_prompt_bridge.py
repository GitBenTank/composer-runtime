"""Regression tests for deterministic music prompts (profile-dominant, same-intent comparison)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_RUNTIME = Path(__file__).resolve().parent.parent
_BRIDGE = _RUNTIME / "bridge"
_DATA = _RUNTIME / "data" / "composers"

for _pkg in (_RUNTIME.parent / "composer-system",):
    if (_pkg / "composer_system").is_dir():
        sys.path.insert(0, str(_pkg.resolve()))
        break
else:
    pytest.skip("composer-system sibling not found", allow_module_level=True)

sys.path.insert(0, str(_BRIDGE))

from composer_system.brief import get_brief  # noqa: E402
from composer_system.load import load_profile  # noqa: E402
from music_prompt_bridge import build_music_prompt  # noqa: E402

_SHARED_INTENT = "a playful symphony with unexpected turns"

# Substrings that must appear in the joined constraints (composer-specific tail).
_CONSTRAINT_MARKERS: dict[str, list[str]] = {
    "bach": ["linear clarity", "counterpoint"],
    "beethoven": ["developmental drama", "motivic narrative"],
    "chopin": ["rubato", "pianistic voicing"],
    "mozart": ["periodic lyricism", "ensemble continuity"],
    "haydn": ["cadential surprises", "motivic cells"],
}


@pytest.mark.parametrize("composer_id", sorted(_CONSTRAINT_MARKERS))
def test_build_music_prompt_constraints_include_composer_specific_phrases(composer_id: str) -> None:
    profile = load_profile(composer_id, data_dir=_DATA)
    brief = get_brief(profile, _SHARED_INTENT)
    mp = build_music_prompt(brief)
    blob = " ".join(mp["constraints"]).lower()
    for needle in _CONSTRAINT_MARKERS[composer_id]:
        assert needle.lower() in blob, f"{composer_id}: missing {needle!r} in constraints"


@pytest.mark.parametrize("composer_id", sorted(_CONSTRAINT_MARKERS))
def test_same_intent_music_prompt_is_deterministic(composer_id: str) -> None:
    profile = load_profile(composer_id, data_dir=_DATA)
    brief = get_brief(profile, _SHARED_INTENT)
    a = build_music_prompt(brief)
    b = build_music_prompt(brief)
    assert a == b


@pytest.mark.parametrize("composer_id", sorted(_CONSTRAINT_MARKERS))
def test_generator_prompt_profiles_seed_before_user_orientation(composer_id: str) -> None:
    profile = load_profile(composer_id, data_dir=_DATA)
    brief = get_brief(profile, _SHARED_INTENT)
    text = build_music_prompt(brief)["generator_prompt"]
    assert "Primary concept seed" in text
    assert "User orientation" in text
    assert text.index("Primary concept seed") < text.index("User orientation")


def test_user_orientation_asks_to_reinterpret_not_obey_literally() -> None:
    profile = load_profile("haydn", data_dir=_DATA)
    brief = get_brief(profile, _SHARED_INTENT)
    gp = build_music_prompt(brief)["generator_prompt"]
    assert "interpret this request strictly through the profile above" in gp
    assert "adapt its terms rather than replacing them" in gp
