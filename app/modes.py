"""Medium modes: pure 2D, pure 3D, or a deliberate 2D/3D hybrid."""

MODES = ("2d", "3d", "hybrid")


def normalize_mode(value: str | None = None, three_d: bool | None = None) -> str:
    if value:
        value = str(value).strip().lower()
        if value in MODES:
            return value
        raise ValueError(f"unknown mode: {value!r}")
    if three_d is not None:
        return "3d" if three_d else "2d"
    return "2d"


def is_3d(mode: str) -> bool:
    return mode in ("3d", "hybrid")


def mode_label(mode: str) -> str:
    return {"2d": "2D", "3d": "3D", "hybrid": "Hybrid"}.get(mode, mode)
