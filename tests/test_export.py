import io
import json
import zipfile

from fastapi.testclient import TestClient

from app import config
from app.export import build_export, build_review_html

GOOD = """<!doctype html><html><head><title>x</title></head><body>BUKAL</body></html>"""


def make_run(mode="2d"):
    return {
        "run_id": "20261103-120000-abcd",
        "brief": "Create an <script>alert(1)</script> logo for Kape",
        "provider": "openrouter",
        "model": "meta/muse-spark-1.3-contributor",
        "created_at": "2026-11-03T12:00:00+00:00",
        "elapsed_ms": 19000,
        "mode": mode,
        "three_d": mode != "2d",
        "cast": ["baseline", "stoic"],
        "usage_total": {
            "prompt_tokens": 1000, "completion_tokens": 2000,
            "total_tokens": 3000, "cost_usd": None, "cost_source": "unknown",
        },
        "results": [
            {
                "persona": {"id": "baseline", "name": "Baseline", "tagline": "No persona.", "color": "#8b98a9"},
                "ok": True, "approach": "plan", "html": GOOD, "error": None,
                "chars": len(GOOD), "elapsed_ms": 5000,
                "usage": {"prompt_tokens": 500, "completion_tokens": 1000,
                          "total_tokens": 1500, "cost_usd": None, "cost_source": "unknown"},
                "direction": {"layout": "centered_hero", "camera": "static", "transition": "hard_cut"},
            },
            {
                "persona": {"id": "stoic", "name": "The Stoic Minimalist", "tagline": "Restraint.", "color": "#4f8cff"},
                "ok": False, "approach": "", "html": "", "error": "ValidationError: nope",
                "chars": 0, "elapsed_ms": 1000, "usage": {}, "direction": {},
            },
        ],
    }


def names(payload: bytes) -> set[str]:
    return set(zipfile.ZipFile(io.BytesIO(payload)).namelist())


def test_2d_export_has_review_run_and_previews():
    archive = zipfile.ZipFile(io.BytesIO(build_export(make_run("2d"))))
    entries = set(archive.namelist())
    assert {"run.json", "review.html", "README.txt"} <= entries
    assert "previews/baseline.html" in entries
    assert "previews/stoic.html" not in entries  # failed results are not exported
    assert not any(entry.startswith("vendor/") for entry in entries)


def test_3d_export_includes_vendor_and_relative_import_map():
    archive = zipfile.ZipFile(io.BytesIO(build_export(make_run("3d"))))
    entries = set(archive.namelist())
    assert "vendor/three.module.js" in entries
    assert "vendor/three.LICENSE" in entries
    preview = archive.read("previews/baseline.html").decode("utf-8")
    assert '"three":"../vendor/three.module.js"' in preview
    assert '"/vendor/three.module.js"' not in preview


def test_review_escapes_the_brief():
    page = build_review_html(make_run("2d"))
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page


def test_review_lists_agents_directions_and_usage():
    page = build_review_html(make_run("2d"))
    assert "Baseline" in page
    assert "The Stoic Minimalist" in page
    assert "centered hero" in page
    assert "8s loop · 1080×1080" in page
    assert "ValidationError: nope" in page


def test_review_shows_the_personality_record():
    run = make_run("2d")
    run["results"][0].update(
        traits={"O": 60, "C": 70, "E": 50, "A": 60, "N": 25},
        style={"density": "balanced", "type_sizes": 3, "colors": 3, "easing": "varied"},
        temperature=0.7,
    )
    page = build_review_html(run)
    assert "O 60" in page
    assert "T 0.7" in page
    assert "balanced · 3 sizes · 3 colors · varied" in page


def test_export_route_returns_a_zip(monkeypatch, tmp_path):
    from app.main import app

    run = make_run("2d")
    monkeypatch.setattr(config, "RUNS_DIR", tmp_path)
    (tmp_path / f"{run['run_id']}.json").write_text(json.dumps(run), encoding="utf-8")

    with TestClient(app) as client:
        response = client.get(f"/runs/{run['run_id']}/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert f"troupe-{run['run_id']}.zip" in response.headers["content-disposition"]
    assert "review.html" in names(response.content)


def test_export_route_404_for_unknown_run():
    from app.main import app

    with TestClient(app) as client:
        response = client.get("/runs/20261103-000000-ffff/export")
    assert response.status_code == 404


def test_export_route_404_for_invalid_id():
    from app.main import app

    with TestClient(app) as client:
        response = client.get("/runs/../../etc/export")
    assert response.status_code == 404
