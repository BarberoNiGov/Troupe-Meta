import pytest

from app.cinema import (
    CAMERAS,
    LAYOUTS,
    PERSONA_DIRECTION,
    TRANSITIONS,
    cinema_prompt,
    direction_for,
    validate_direction,
)
from app.personas import PERSONAS


def test_persona_direction_covers_full_roster():
    assert set(PERSONA_DIRECTION) == {p["id"] for p in PERSONAS}
    for persona in PERSONAS:
        direction = direction_for(persona["id"])
        assert direction["layout"] in LAYOUTS
        assert direction["camera"] in CAMERAS
        assert direction["transition"] in TRANSITIONS


def test_validate_direction_accepts_and_normalizes():
    direction = validate_direction({
        "layout": "ORBIT_STAGE",
        "camera": "Slow_Push_In",
        "transition": "Match_Cut",
    })
    assert direction == {
        "layout": "orbit_stage",
        "camera": "slow_push_in",
        "transition": "match_cut",
    }


def test_validate_direction_rejects_missing_or_unknown():
    with pytest.raises(ValueError):
        validate_direction({"layout": "centered_hero", "camera": "static"})
    with pytest.raises(ValueError):
        validate_direction({"layout": "nope", "camera": "static", "transition": "hard_cut"})


def test_cinema_prompt_mentions_both_modes_and_suggestion():
    prompt_2d = cinema_prompt("romantic", three_d=False)
    prompt_3d = cinema_prompt("romantic", three_d=True)
    assert "2D layouts" in prompt_2d
    assert "3D layouts" in prompt_3d
    assert "layout=diorama" in prompt_2d
    assert "camera=slow_push_in" in prompt_2d
    assert "transition=dissolve" in prompt_2d
