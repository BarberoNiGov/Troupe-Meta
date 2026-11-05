"""Run the cast on one brief and print a spike summary with token usage.

    python scripts/spike.py
    python scripts/spike.py --cast baseline,anxious,feral,stoic,hype,accessibility,deadpan,romantic
    python scripts/spike.py --brief "..." --provider openrouter
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config  # noqa: E402
from app.generate import run_room  # noqa: E402
from app.personas import DEFAULT_CAST  # noqa: E402


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def fmt_cost(cost, source) -> str:
    if cost is None:
        return "n/a"
    body = f"${cost:.6f}" if cost < 0.01 else f"${cost:.4f}"
    return f"est. {body}" if source in ("estimated", "mixed") else body


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", default=config.DEFAULT_BRIEF)
    parser.add_argument("--provider", default=None)
    parser.add_argument("--cast", default=",".join(DEFAULT_CAST),
                        help="comma-separated persona ids")
    parser.add_argument("--mode", choices=["2d", "3d", "hybrid"], default="2d",
                        help="medium mode (default: 2d)")
    args = parser.parse_args()
    cast = [part.strip() for part in args.cast.split(",") if part.strip()]

    print(f"provider: {config.provider_label()}")
    print(f"cast:     {len(cast)} agents")
    print(f"mode:     {args.mode.upper()}" + (" · Three.js r160" if args.mode in ("3d", "hybrid") else " · CSS/SVG"))
    print(f"brief:    {args.brief}\n")

    run = await run_room(args.brief, args.provider, persona_ids=cast, mode=args.mode)
    ok = 0
    for result in run["results"]:
        persona = result["persona"]
        usage = result.get("usage") or {}
        if result["ok"]:
            ok += 1
            print(
                f"[OK]   {persona['name']:<28} "
                f"{fmt_tokens(usage.get('prompt_tokens', 0)):>7} in  "
                f"{fmt_tokens(usage.get('completion_tokens', 0)):>7} out  "
                f"{fmt_cost(usage.get('cost_usd'), usage.get('cost_source')):>12}  "
                f"{result['elapsed_ms']:>6} ms"
            )
            print(f"       {result['approach'][:150]}")
            direction = result.get("direction") or {}
            print(f"       {direction.get('layout', '?')} · {direction.get('camera', '?')} · "
                  f"{direction.get('transition', '?')}")
        else:
            print(f"[FAIL] {persona['name']:<28} {result['error']}")

    total = run.get("usage_total") or {}
    print(f"\n{ok}/{len(run['results'])} generated in {run['elapsed_ms']} ms")
    print(
        f"tokens: {fmt_tokens(total.get('prompt_tokens', 0))} in / "
        f"{fmt_tokens(total.get('completion_tokens', 0))} out · "
        f"cost: {fmt_cost(total.get('cost_usd'), total.get('cost_source'))} "
        f"({total.get('cost_source', 'unknown')})"
    )
    print(f"run: {run['run_id']}")
    print(f"saved: {config.RUNS_DIR / (run['run_id'] + '.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
