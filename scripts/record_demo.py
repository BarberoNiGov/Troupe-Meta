"""Record a silent studio demo: cast + usage -> blind vote -> reveal."""

import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "video"
OUT.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8030"


def launch(p):
    for channel in ("msedge", "chrome"):
        try:
            return p.chromium.launch(channel=channel, headless=True)
        except Exception:
            continue
    return p.chromium.launch(headless=True)


def main() -> int:
    with sync_playwright() as p:
        browser = launch(p)
        context = browser.new_context(
            viewport={"width": 1440, "height": 1600},
            record_video_dir=str(OUT),
            record_video_size={"width": 1440, "height": 1600},
            device_scale_factor=1,
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(4200)

        # Show the usage monitor.
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2600)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1600)

        # Blind vote.
        page.locator("#blind").check()
        page.wait_for_timeout(2600)
        page.locator(".vote-btn:visible").nth(1).click()
        page.wait_for_timeout(1200)
        page.locator("#reveal").click()
        page.wait_for_timeout(4000)

        video_path = page.video.path()
        context.close()
        browser.close()

    video = Path(video_path)
    mp4 = ROOT / "docs" / "demo.mp4"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(video), "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-movflags", "+faststart", str(mp4)],
            check=True, capture_output=True,
        )
        print(f"wrote {mp4}")
    except Exception as exc:  # noqa: BLE001
        print(f"video saved at {video} (ffmpeg failed: {exc})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
