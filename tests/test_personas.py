from app.personas import (
    DEFAULT_CAST,
    FLAVOR_PACK,
    PERSONAS,
    get_persona,
    personas_for,
    public_personas,
    temperature_for,
    trait_block,
)


def test_eleven_personas():
    assert len(PERSONAS) == 11
    assert len({p["id"] for p in PERSONAS}) == 11


def test_default_cast_is_eight():
    assert len(DEFAULT_CAST) == 8
    assert len(set(DEFAULT_CAST)) == 8


def test_flavor_pack_is_three():
    assert len(FLAVOR_PACK) == 3
    assert all(get_persona(pid)["pack"] == "flavor" for pid in FLAVOR_PACK)


def test_public_personas_hide_prompts():
    public = public_personas()
    assert all("prompt" not in p for p in public)
    assert all("temperature" not in p for p in public)
    assert all("pack" in p for p in public)


def test_personas_for_preserves_order_and_rejects_unknown():
    selected = personas_for(["hype", "baseline", "stoic"])
    assert [p["id"] for p in selected] == ["hype", "baseline", "stoic"]
    try:
        personas_for(["nope"])
    except ValueError:
        pass
    else:
        raise AssertionError("unknown persona must raise")


def test_get_persona():
    assert get_persona("anxious")["name"] == "The Anxious Perfectionist"
    assert get_persona("nope") is None


def test_every_persona_has_a_complete_record():
    traits = {"O", "C", "E", "A", "N"}
    densities = {"sparse", "balanced", "dense"}
    easings = {"one_curve", "varied", "spring"}
    risks = {"low", "medium", "high"}
    for persona in PERSONAS:
        assert set(persona["traits"]) == traits
        assert all(0 <= score <= 100 for score in persona["traits"].values())
        assert persona["reads_as"]
        style = persona["style"]
        assert style["density"] in densities
        assert style["easing"] in easings
        assert style["risk"] in risks
        assert 1 <= style["type_sizes"] <= 8
        assert 1 <= style["colors"] <= 6
        assert style["refuse"]


def test_temperature_is_derived_and_bounded():
    for persona in PERSONAS:
        assert "temperature" not in persona  # the record is the only source
        assert 0.3 <= temperature_for(persona) <= 1.0
    assert temperature_for(get_persona("feral")) > temperature_for(get_persona("stoic"))
    assert temperature_for(get_persona("baseline")) == 0.7


def test_trait_block_is_deterministic_and_states_the_precedence():
    persona = get_persona("anxious")
    first = trait_block(persona)
    assert first == trait_block(persona)
    assert "TRAIT PROFILE" in first
    assert "DESIGN KERNEL" in first
    assert "O 45" in first
    assert "outranks this kernel" in first


def test_system_prompt_includes_the_trait_block():
    from app.providers.base import Provider

    prompt = Provider().system_prompt(get_persona("stoic"))
    assert "TRAIT PROFILE" in prompt
    assert "DESIGN KERNEL" in prompt
    assert "YOUR TEMPERAMENT" in prompt
