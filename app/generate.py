"""Run the room: one brief, many agents, in parallel."""

import asyncio
import json
import re
import secrets
import time
from datetime import datetime, timezone

from app import config
from app.modes import is_3d, normalize_mode
from app.personas import DEFAULT_CAST, public_personas, personas_for, temperature_for
from app.providers import get_provider
from app.providers.base import ProviderError
from app.usage import aggregate_usage, empty_usage
from app.validate import ValidationError, validate_generation

_RUN_ID = re.compile(r"^[a-z0-9-]+$")


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{secrets.token_hex(2)}"


async def generate_one(provider, persona: dict, brief: str, mode: str = "2d") -> dict:
    started = time.perf_counter()
    result = {
        "persona": {k: persona[k] for k in ("id", "name", "tagline", "color")},
        "traits": dict(persona["traits"]),
        "style": dict(persona["style"]),
        "temperature": temperature_for(persona),
        "ok": False,
        "approach": "",
        "html": "",
        "error": None,
        "chars": 0,
        "elapsed_ms": 0,
        "usage": empty_usage(),
        "direction": {},
    }
    def retryable(exc: Exception) -> bool:
        text = str(exc).lower()
        return (
            "invalid json" in text
            or "expecting" in text
            or "unterminated" in text
            or "invalid or missing layout" in text
            or "invalid or missing camera" in text
            or "invalid or missing transition" in text
        )

    for attempt in range(2):
        try:
            raw = await provider.generate(persona, brief, mode)
            usage = raw.get("usage") or empty_usage()
            approach, html, direction = validate_generation(raw, mode=mode)
            result.update(
                ok=True, approach=approach, html=html, chars=len(html),
                usage=usage, direction=direction, error=None,
            )
            break
        except (ProviderError, ValidationError) as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
            result["usage"] = empty_usage()
            result["direction"] = {}
            if attempt == 0 and retryable(exc):
                continue
            break
        except Exception as exc:  # noqa: BLE001 - one agent must not kill the room
            result["error"] = f"{type(exc).__name__}: {exc}"
            result["usage"] = empty_usage()
            result["direction"] = {}
            break
    result["elapsed_ms"] = round((time.perf_counter() - started) * 1000)
    return result


async def run_room(brief: str, provider_name: str | None = None,
                   persona_ids: list[str] | None = None, mode: str = "2d") -> dict:
    mode = normalize_mode(mode)
    three_d = is_3d(mode)
    brief = (brief or "").strip()
    if not brief:
        raise ValueError("brief is required")
    if len(brief) > 800:
        raise ValueError("brief must be 800 characters or fewer")

    selected = personas_for(persona_ids or DEFAULT_CAST)
    if len(selected) < 3:
        raise ValueError("choose at least 3 agents")
    if len(selected) > config.MAX_CAST:
        raise ValueError(f"choose at most {config.MAX_CAST} agents")

    provider = get_provider(provider_name)
    run_id = new_run_id()
    started = time.perf_counter()
    semaphore = asyncio.Semaphore(max(1, config.MAX_CONCURRENCY))

    async def one(persona: dict) -> dict:
        async with semaphore:
            return await generate_one(provider, persona, brief, mode=mode)

    results = await asyncio.gather(*(one(p) for p in selected))
    run = {
        "run_id": run_id,
        "brief": brief,
        "provider": provider.name,
        "model": provider.model,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_ms": round((time.perf_counter() - started) * 1000),
        "mode": mode,
        "three_d": bool(three_d),
        "cast": [p["id"] for p in selected],
        "usage_total": aggregate_usage([r["usage"] for r in results]),
        "results": results,
    }
    save_run(run)
    return run


def save_run(run: dict) -> None:
    config.ensure_dirs()
    run_dir = config.RUNS_DIR / run["run_id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    for result in run["results"]:
        if result["ok"]:
            (run_dir / f"{result['persona']['id']}.html").write_text(
                result["html"], encoding="utf-8"
            )
    (config.RUNS_DIR / f"{run['run_id']}.json").write_text(
        json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_run(run_id: str) -> dict | None:
    if not _RUN_ID.match(run_id or ""):
        return None
    path = config.RUNS_DIR / f"{run_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def latest_run() -> dict | None:
    config.ensure_dirs()
    files = sorted(config.RUNS_DIR.glob("*.json"))
    if not files:
        return None
    return json.loads(files[-1].read_text(encoding="utf-8"))


def preview_html(run_id: str, persona_id: str) -> str | None:
    run = load_run(run_id)
    if not run:
        return None
    for result in run["results"]:
        if result["persona"]["id"] == persona_id and result["ok"]:
            return result["html"]
    return None


def empty_public_run() -> dict:
    return {
        "personas": public_personas(),
        "default_cast": DEFAULT_CAST,
        "brief": config.DEFAULT_BRIEF,
        "provider": config.LLM_PROVIDER,
        "provider_label": config.provider_label(),
    }
