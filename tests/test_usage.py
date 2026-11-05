from app.usage import aggregate_usage, empty_usage, normalize_usage


def test_provider_reported_cost():
    usage = normalize_usage({
        "prompt_tokens": 1000,
        "completion_tokens": 2000,
        "total_tokens": 3000,
        "cost": 0.0012,
    })
    assert usage["cost_source"] == "provider"
    assert usage["cost_usd"] == 0.0012
    assert usage["total_tokens"] == 3000


def test_estimated_cost():
    usage = normalize_usage({
        "prompt_tokens": 1_000_000,
        "completion_tokens": 500_000,
        "total_tokens": 1_500_000,
    }, input_price_per_m=0.10, output_price_per_m=0.20)
    assert usage["cost_source"] == "estimated"
    assert abs(usage["cost_usd"] - 0.20) < 1e-9


def test_unknown_cost():
    usage = normalize_usage({"prompt_tokens": 10, "completion_tokens": 20})
    assert usage["cost_source"] == "unknown"
    assert usage["cost_usd"] is None


def test_empty_usage():
    usage = empty_usage()
    assert usage["total_tokens"] == 0
    assert usage["cost_usd"] is None


def test_aggregate_usage():
    a = normalize_usage({"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300, "cost": 0.001})
    b = normalize_usage({"prompt_tokens": 400, "completion_tokens": 500, "total_tokens": 900, "cost": 0.002})
    total = aggregate_usage([a, b])
    assert total["prompt_tokens"] == 500
    assert total["completion_tokens"] == 700
    assert total["total_tokens"] == 1200
    assert abs(total["cost_usd"] - 0.003) < 1e-9
    assert total["cost_source"] == "provider"


def test_aggregate_mixed_sources():
    a = normalize_usage({"prompt_tokens": 10, "completion_tokens": 10, "cost": 0.001})
    b = normalize_usage({"prompt_tokens": 10, "completion_tokens": 10}, 1.0, 1.0)
    total = aggregate_usage([a, b])
    assert total["cost_source"] == "mixed"
