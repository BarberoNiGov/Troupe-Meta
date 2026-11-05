"""FastAPI entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from app import config
from app.export import build_export
from app.generate import latest_run, load_run, preview_html, run_room
from app.modes import MODES, normalize_mode
from app.personas import DEFAULT_CAST, FLAVOR_PACK, public_personas


@asynccontextmanager
async def lifespan(_: FastAPI):
    config.ensure_dirs()
    yield


app = FastAPI(title="Troupe", description="A room of persona-conditioned coding agents.", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(config.STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "provider": config.LLM_PROVIDER, "provider_label": config.provider_label()}


@app.get("/config")
def get_config() -> dict:
    return {
        "personas": public_personas(),
        "default_cast": DEFAULT_CAST,
        "flavor_pack": FLAVOR_PACK,
        "max_cast": config.MAX_CAST,
        "modes": list(MODES),
        "mode_default": "2d",
        "three_d_default": False,
        "brief": config.DEFAULT_BRIEF,
        "provider": config.LLM_PROVIDER,
        "provider_label": config.provider_label(),
        "experiment": "Does persona conditioning change coding-agent output?",
    }


@app.post("/run")
async def run(payload: dict) -> JSONResponse:
    brief = str(payload.get("brief", "")).strip()
    persona_ids = payload.get("persona_ids")
    if persona_ids is not None:
        if not isinstance(persona_ids, list) or not all(isinstance(p, str) for p in persona_ids):
            raise HTTPException(status_code=400, detail="persona_ids must be a list of strings")
    three_d = payload.get("three_d", None)
    if three_d is not None and not isinstance(three_d, bool):
        raise HTTPException(status_code=400, detail="three_d must be a boolean")
    try:
        mode = normalize_mode(payload.get("mode"), three_d)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        result = await run_room(brief, persona_ids=persona_ids, mode=mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}") from exc
    return JSONResponse(result)


@app.get("/latest")
def latest() -> JSONResponse:
    run = latest_run()
    if not run:
        return JSONResponse({"error": "no runs yet"}, status_code=404)
    return JSONResponse(run)


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> JSONResponse:
    run = load_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return JSONResponse(run)


@app.get("/runs/{run_id}/export")
def export_run(run_id: str) -> Response:
    run = load_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return Response(
        content=build_export(run),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="troupe-{run_id}.zip"'},
    )


@app.get("/preview/{run_id}/{persona_id}", response_class=HTMLResponse)
def preview(run_id: str, persona_id: str) -> HTMLResponse:
    html = preview_html(run_id, persona_id)
    if not html:
        raise HTTPException(status_code=404, detail="preview not found")
    return HTMLResponse(html)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8030, reload=True)
