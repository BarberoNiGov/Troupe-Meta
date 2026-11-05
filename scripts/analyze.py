"""Measure how different the five outputs actually look.

    python scripts/analyze.py
    python scripts/analyze.py --run 20261103-...

Uses the 4s screenshots produced by render_check.py when available:
- visual similarity: colour histogram intersection + 8x8 layout distance
- palette similarity: Jaccard overlap of hex colours in the HTML

Lower similarity = more diversity. This is a pilot metric, not a proof.
"""

import argparse
import itertools
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config  # noqa: E402

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

_HEX = re.compile(r"#[0-9a-fA-F]{6}\b")


def latest_run_id() -> str | None:
    files = sorted(config.RUNS_DIR.glob("*.json"))
    return files[-1].stem if files else None


def palette(html: str) -> set[str]:
    return {c.lower() for c in _HEX.findall(html)}


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _rgb_pixels(image):
    raw = image.tobytes()
    return [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 3)]


def visual_signature(path: Path):
    if not Image or not path.exists():
        return None
    image = Image.open(path).convert("RGB").resize((64, 64))
    hist = [0] * 512
    for r, g, b in _rgb_pixels(image):
        hist[(r // 32) * 64 + (g // 32) * 8 + (b // 32)] += 1
    total = sum(hist) or 1
    hist = [v / total for v in hist]
    grid = _rgb_pixels(image.resize((8, 8)))
    return hist, grid


def visual_similarity(a, b) -> float:
    if a is None or b is None:
        return 1.0
    hist_a, grid_a = a
    hist_b, grid_b = b
    hist_sim = sum(min(x, y) for x, y in zip(hist_a, hist_b))
    diff = sum(abs(x - y) for pa, pb in zip(grid_a, grid_b) for x, y in zip(pa, pb))
    grid_sim = 1 - diff / (8 * 8 * 3 * 255)
    return (hist_sim + grid_sim) / 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default=None)
    args = parser.parse_args()
    run_id = args.run or latest_run_id()
    if not run_id:
        print("no runs found")
        return 1
    run = json.loads((config.RUNS_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    out_dir = config.RUNS_DIR / run_id
    outputs = []
    for result in run["results"]:
        if not result["ok"]:
            continue
        name = result["persona"]["name"]
        pid = result["persona"]["id"]
        shot = out_dir / f"{pid}-4s.png"
        if not shot.exists():
            shot = out_dir / f"{pid}-1s.png"
        outputs.append((name, result["html"], visual_signature(shot)))

    if len(outputs) < 2:
        print("not enough outputs to compare")
        return 1

    print(f"run: {run_id}  ({len(outputs)} outputs)\n")
    print(f"{'pair':<56} {'visual':>7} {'palette':>8}")
    visual_scores = []
    palette_scores = []
    for (name_a, html_a, vis_a), (name_b, html_b, vis_b) in itertools.combinations(outputs, 2):
        v = visual_similarity(vis_a, vis_b)
        p = jaccard(palette(html_a), palette(html_b))
        visual_scores.append(v)
        palette_scores.append(p)
        label = f"{name_a[:26]} / {name_b[:26]}"
        print(f"{label:<56} {v:>7.2f} {p:>8.2f}")

    print(f"\naverage visual similarity:  {sum(visual_scores)/len(visual_scores):.2f}")
    print(f"average palette similarity: {sum(palette_scores)/len(palette_scores):.2f}")
    print("(1.00 = identical, 0.00 = no overlap)")

    baseline = next(((n, h, v) for n, h, v in outputs if n == "Baseline"), None)
    if baseline:
        print("\ndistance from the neutral baseline:")
        for name, html, vis in outputs:
            if name == "Baseline":
                continue
            v = 1 - visual_similarity(baseline[2], vis)
            p = 1 - jaccard(palette(baseline[1]), palette(html))
            print(f"  {name:<28} visual {v:.2f}  palette {p:.2f}")

    print("\ndirection:")
    print(f"  {'agent':<28} {'layout':<22} {'camera':<20} {'transition':<14}")
    from collections import Counter
    for result in run["results"]:
        if not result.get("ok"):
            continue
        d = result.get("direction") or {}
        print(f"  {result['persona']['name'][:28]:<28} {d.get('layout', 'n/a'):<22} "
              f"{d.get('camera', 'n/a'):<20} {d.get('transition', 'n/a'):<14}")
    for axis in ("layout", "camera", "transition"):
        counts = Counter((r.get("direction") or {}).get(axis) for r in run["results"]
                         if r.get("ok") and (r.get("direction") or {}).get(axis))
        if counts:
            print(f"  {axis} counts: {dict(counts)}")

    print("\nusage:")
    print(f"  {'agent':<28} {'in':>8} {'out':>8} {'cost':>12} {'time':>7}")
    total_tokens = 0
    total_cost = 0.0
    cost_known = True
    for result in run["results"]:
        if not result.get("ok"):
            continue
        usage = result.get("usage") or {}
        prompt = usage.get("prompt_tokens", 0) or 0
        completion = usage.get("completion_tokens", 0) or 0
        cost = usage.get("cost_usd")
        if cost is None:
            cost_known = False
            cost_text = "n/a"
        else:
            total_cost += cost
            cost_text = f"${cost:.6f}" if cost < 0.01 else f"${cost:.4f}"
        total_tokens += prompt + completion
        print(f"  {result['persona']['name'][:28]:<28} {prompt:>8,} {completion:>8,} "
              f"{cost_text:>12} {result['elapsed_ms']/1000:>6.1f}s")
    print(f"  {'TOTAL':<28} {'':>8} {'':>8} "
          f"{(f'${total_cost:.6f}' if cost_known else 'partial'):>12}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
