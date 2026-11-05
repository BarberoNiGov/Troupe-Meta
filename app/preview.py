"""Isolated preview origin for generated HTML and vendored Three.js.

Run on 127.0.0.1:8031. It serves only:
  /health
  /vendor/three.module.js
  /vendor/three.LICENSE
  /preview/{run_id}/{persona_id}

It has no API, no secrets, and no directory browsing. The studio embeds these
previews from a different origin, so same-origin access stays inside this
sandboxed preview server.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from app import config
from app.generate import load_run
from app.three import FRAME_ANCESTORS, PREVIEW_CSP, build_preview_html

app = FastAPI(title="Troupe Preview")

VENDOR_DIR = config.ROOT / "app" / "vendor"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "preview"}


@app.get("/vendor/three.module.js")
def three_module() -> FileResponse:
    path = VENDOR_DIR / "three.module.js"
    if not path.exists():
        raise HTTPException(status_code=404, detail="three.module.js not found")
    return FileResponse(path, media_type="text/javascript",
                        headers={"Cache-Control": "public, max-age=86400"})


@app.get("/vendor/three.LICENSE")
def three_license() -> FileResponse:
    path = VENDOR_DIR / "three.LICENSE"
    if not path.exists():
        raise HTTPException(status_code=404, detail="three.LICENSE not found")
    return FileResponse(path, media_type="text/plain")


@app.get("/preview/{run_id}/{persona_id}", response_class=HTMLResponse)
def preview(run_id: str, persona_id: str) -> HTMLResponse:
    run = load_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    result = next(
        (r for r in run.get("results", []) if r.get("persona", {}).get("id") == persona_id),
        None,
    )
    if not result or not result.get("ok"):
        raise HTTPException(status_code=404, detail="preview not found")
    html = build_preview_html(result.get("html", ""))
    return HTMLResponse(
        html,
        headers={
            "Content-Security-Policy": f"{PREVIEW_CSP} {FRAME_ANCESTORS}",
            "Cache-Control": "no-store",
        },
    )
