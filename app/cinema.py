"""Shared direction grammar: layout, camera, transition, beat sheet, persona bias.

Always on for both 2D and 3D runs. The persona suggests a direction; the agent
must declare one valid value on each axis.
"""

LAYOUTS = {
    "centered_hero": "One centered subject; clean symmetric lockup.",
    "editorial": "Off-center subject with deliberate imbalance and type hierarchy.",
    "kinetic_grid": "A modular grid where type and shapes snap into cells.",
    "split_diptych": "Two panels in tension; the mark resolves between them.",
    "frame_within_frame": "A portal, ring, or frame isolates the wordmark.",
    "negative_space": "Mostly empty; the mark earns a small, precise area.",
    "type_as_image": "The wordmark itself is the visual texture.",
    "diagonal": "A diagonal leading line carries the eye to the mark.",
    "orbit_stage": "Hero object centered; props orbit or arc around it.",
    "depth_corridor": "Camera looks down a receding corridor of shapes.",
    "diorama": "A small staged set with floor, backdrop, and hero object.",
    "floating_sculpture": "No floor; the mark is suspended in open space.",
    "type_as_environment": "The letters are architecture; the camera moves through them.",
    "layered_parallax": "Foreground, subject, and background at distinct depths.",
    "top_down_table": "Camera looks down at a styled surface and props.",
}

CAMERAS = {
    "static": "Locked-off frame; motion happens inside it.",
    "slow_push_in": "A slow move toward the subject.",
    "pull_out": "Start close, reveal the wider stage.",
    "orbit_90": "A quarter orbit around the subject.",
    "orbit_180": "A half orbit around the subject.",
    "truck_left": "Lateral move left, keeping the subject framed.",
    "truck_right": "Lateral move right.",
    "pedestal_up": "Vertical rise of the camera.",
    "pedestal_down": "Vertical drop of the camera.",
    "crane_rise": "Start low and rise over the scene.",
    "top_down_descent": "Start above and descend toward the subject.",
    "low_angle_rise": "Start low and tilt/rise into the hero.",
    "parallax_drift": "Gentle lateral drift with depth separation.",
    "whip_pan": "Fast lateral whip with motion blur.",
    "crash_zoom": "Aggressive zoom toward the mark.",
}

TRANSITIONS = {
    "hard_cut": "Immediate change between beats.",
    "match_cut": "A shape or motion match carries one beat into the next.",
    "whip": "Motion-blurred lateral handoff.",
    "iris": "Circular reveal or close.",
    "glitch": "Digital tearing or RGB split.",
    "dissolve": "Soft crossfade between states.",
    "mask_wipe": "A shape mask reveals the next beat.",
    "shutter": "A shutter or bar sweeps the frame.",
}

BEAT_SHEET = (
    "0.0–1.5s establish the stage and light; "
    "1.5–4.0s reveal the wordmark with the declared camera move; "
    "4.0–6.0s hold the brand legible and let the motion settle; "
    "6.0–8.0s resolve back to the opening pose for a seamless loop."
)

PERSONA_DIRECTION = {
    "baseline": {"layout": "centered_hero", "camera": "slow_push_in", "transition": "match_cut"},
    "anxious": {"layout": "centered_hero", "camera": "static", "transition": "hard_cut"},
    "feral": {"layout": "type_as_environment", "camera": "whip_pan", "transition": "glitch"},
    "stoic": {"layout": "negative_space", "camera": "static", "transition": "dissolve"},
    "hype": {"layout": "orbit_stage", "camera": "orbit_180", "transition": "whip"},
    "accessibility": {"layout": "centered_hero", "camera": "parallax_drift", "transition": "dissolve"},
    "deadpan": {"layout": "centered_hero", "camera": "static", "transition": "hard_cut"},
    "romantic": {"layout": "diorama", "camera": "slow_push_in", "transition": "dissolve"},
    "archivist": {"layout": "frame_within_frame", "camera": "parallax_drift", "transition": "iris"},
    "corporate": {"layout": "centered_hero", "camera": "slow_push_in", "transition": "hard_cut"},
    "speedrunner": {"layout": "centered_hero", "camera": "static", "transition": "hard_cut"},
}

LAYOUT_NAMES = tuple(LAYOUTS)
CAMERA_NAMES = tuple(CAMERAS)
TRANSITION_NAMES = tuple(TRANSITIONS)


def direction_for(persona_id: str) -> dict:
    return PERSONA_DIRECTION.get(
        persona_id,
        {"layout": "centered_hero", "camera": "slow_push_in", "transition": "match_cut"},
    )


def validate_direction(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("direction must be a JSON object")
    layout = str(data.get("layout", "")).strip().lower()
    camera = str(data.get("camera", "")).strip().lower()
    transition = str(data.get("transition", "")).strip().lower()
    if not layout or layout not in LAYOUTS:
        raise ValueError(f"invalid or missing layout: {layout!r}")
    if not camera or camera not in CAMERAS:
        raise ValueError(f"invalid or missing camera: {camera!r}")
    if not transition or transition not in TRANSITIONS:
        raise ValueError(f"invalid or missing transition: {transition!r}")
    return {"layout": layout, "camera": camera, "transition": transition}


def cinema_prompt(persona_id: str, three_d: bool = False) -> str:
    suggestion = direction_for(persona_id)
    mode_layouts = (
        "3D layouts: orbit_stage, depth_corridor, diorama, floating_sculpture, "
        "type_as_environment, layered_parallax, frame_within_frame, top_down_table, centered_hero."
        if three_d
        else "2D layouts: centered_hero, editorial, kinetic_grid, split_diptych, "
             "frame_within_frame, negative_space, type_as_image, diagonal."
    )
    camera_note = (
        "3D translation: drive the actual Three.js camera along that move."
        if three_d
        else "2D translation: push/pull = scale, truck = lateral translate, pedestal = "
             "vertical translate, parallax = layered translate, whip = fast translate + blur, "
             "crash_zoom = scale spike."
    )
    return f"""DIRECTION GRAMMAR (always on)

Choose exactly one layout, one camera, and one transition. Declare them in the JSON.

{mode_layouts}

Cameras: {", ".join(CAMERA_NAMES)}.
{camera_note}

Transitions: {", ".join(TRANSITION_NAMES)}.

Beat sheet: {BEAT_SHEET}
The brand name must stay legible for at least 5 of the 8 seconds.

Your temperament suggests: layout={suggestion['layout']}, camera={suggestion['camera']},
transition={suggestion['transition']}. Use it unless the brief demands otherwise.
Do not default to the same orbit/ring composition for every 3D run.
"""
