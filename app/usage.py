"""Token and cost accounting. Tokens are exact; cost is reported or estimated."""

from typing import Any


def empty_usage() -> dict:
    return {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cost_usd": None,
        "cost_source": "unknown",
        "cache_hit_tokens": 0,
        "cache_miss_tokens": 0,
    }


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def normalize_usage(raw: dict | None, input_price_per_m: float = 0.0,
                    output_price_per_m: float = 0.0) -> dict:
    """Turn a provider usage block into a stable shape.

    OpenRouter reports a cost; direct model routes may not. When no cost is
    reported, estimate it only if prices are configured (per million tokens).
    """
    raw = raw or {}
    prompt = _as_int(raw.get("prompt_tokens") or raw.get("input_tokens"))
    completion = _as_int(raw.get("completion_tokens") or raw.get("output_tokens"))
    total = _as_int(raw.get("total_tokens")) or prompt + completion
    cost = raw.get("cost", raw.get("total_cost"))
    source = None
    if isinstance(cost, (int, float)):
        cost = float(cost)
        source = "provider"
    elif isinstance(cost, str):
        try:
            cost = float(cost)
            source = "provider"
        except ValueError:
            cost = None
    if cost is None and (input_price_per_m or output_price_per_m):
        cost = (prompt / 1_000_000) * input_price_per_m + (completion / 1_000_000) * output_price_per_m
        source = "estimated"
    if cost is None:
        source = "unknown"
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "cost_usd": round(cost, 8) if cost is not None else None,
        "cost_source": source or "unknown",
        "cache_hit_tokens": _as_int(raw.get("prompt_cache_hit_tokens")),
        "cache_miss_tokens": _as_int(raw.get("prompt_cache_miss_tokens")),
    }


def aggregate_usage(usages: list[dict]) -> dict:
    prompt = sum(_as_int(u.get("prompt_tokens")) for u in usages)
    completion = sum(_as_int(u.get("completion_tokens")) for u in usages)
    total = sum(_as_int(u.get("total_tokens")) for u in usages)
    costs = [u.get("cost_usd") for u in usages if u.get("cost_usd") is not None]
    sources = [u.get("cost_source") for u in usages if u.get("cost_usd") is not None]
    cost = round(sum(costs), 8) if costs else None
    if not costs:
        source = "unknown"
    elif all(s == "provider" for s in sources):
        source = "provider"
    elif all(s == "estimated" for s in sources):
        source = "estimated"
    else:
        source = "mixed"
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "cost_usd": cost,
        "cost_source": source,
    }
