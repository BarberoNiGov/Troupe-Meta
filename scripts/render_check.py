"""Render each generated HTML in a real browser and report errors.

    python scripts/render_check.py
    python scripts/render_check.py --run 20261103-...

Requires Playwright. On Windows this tries Edge first.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config  # noqa: E402

from playwright.sync_api import sync_playwright  # noqa: E402
from PIL import Image  # noqa: E402


def mean_brightness(path: Path) -> float:
    image = Image.open(path).convert("RGB").resize((64, 64))
    raw = image.tobytes()
    total = sum(raw)
    return total / len(raw) if raw else 0.0


def launch(p):
    for channel in ("msedge", "chrome"):
        try:
            return p.chromium.launch(channel=channel, headless=True)
        except Exception:
            continue
    return p.chromium.launch(headless=True)


def latest_run_id() -> str | None:
    files = sorted(config.RUNS_DIR.glob("*.json"))
    return files[-1].stem if files else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default=None)
    args = parser.parse_args()
    run_id = args.run or latest_run_id()
    if not run_id:
        print("no runs found")
        return 1
    run_path = config.RUNS_DIR / f"{run_id}.json"
    if not run_path.exists():
        print(f"run not found: {run_id}")
        return 1
    run = json.loads(run_path.read_text(encoding="utf-8"))
    mode = run.get("mode") or ("3d" if run.get("three_d") else "2d")
    out_dir = config.RUNS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = launch(p)
        for result in run["results"]:
            persona = result["persona"]
            if not result["ok"]:
                print(f"[SKIP] {persona['name']:<28} generation failed")
                continue
            context = browser.new_context(viewport={"width": 1080, "height": 1080}, device_scale_factor=1)
            context.set_default_timeout(20000)
            page = context.new_page()
            errors = []
            page.on("console", lambda msg: errors.append(f"console:{msg.type}:{msg.text}") if msg.type == "error" else None)
            page.on("pageerror", lambda err: errors.append(f"pageerror:{err}"))
            try:
                if mode != "2d":
                    page.goto(f"http://127.0.0.1:8031/preview/{run_id}/{persona['id']}",
                              wait_until="networkidle", timeout=30000)
                else:
                    page.set_content(result["html"], wait_until="load")
                page.wait_for_timeout(1000)
                shot1 = out_dir / f"{persona['id']}-1s.png"
                page.screenshot(path=str(shot1))
                page.wait_for_timeout(3000)
                shot4 = out_dir / f"{persona['id']}-4s.png"
                page.screenshot(path=str(shot4))
                body_chars = page.evaluate("() => document.body ? document.body.innerText.length : 0")
                animations = page.evaluate("() => document.getAnimations ? document.getAnimations().length : 0")
                elements = page.evaluate("() => document.querySelectorAll('*').length")
                canvas = page.evaluate("""() => {
                  const c = document.querySelector('canvas');
                  if (!c) return null;
                  let gl = null;
                  try { gl = c.getContext('webgl2') || c.getContext('webgl'); } catch (e) {}
                  return {w: c.width, h: c.height, gl: !!gl};
                }""")
                bright = mean_brightness(shot4)
                label = mode.upper()
                print(f"[{'OK' if not errors else 'ERR'}] {persona['name']:<28} {label} "
                      f"errors={len(errors):<2} anims={animations:<3} elements={elements:<5} "
                      f"text={body_chars} canvas={canvas} bright={bright:.1f}")
                if mode != "2d" and (not canvas or not canvas.get("gl")):
                    print("      WARNING: no WebGL canvas detected")
                if bright < 5:
                    print("      WARNING: screenshot is nearly black")
                for err in errors[:3]:
                    print(f"      {err[:200]}")
            except Exception as exc:  # noqa: BLE001
                print(f"[FAIL] {persona['name']:<28} {type(exc).__name__}: {exc}")
            finally:
                context.close()
        browser.close()
    print(f"\nscreenshots: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
