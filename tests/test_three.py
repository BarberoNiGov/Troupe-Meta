import pytest

from app.personas import get_persona
from app.providers.base import Provider
from app.three import build_preview_html, validate_three_imports
from app.validate import ValidationError, validate_html


def three_html(import_from: str = "three") -> str:
    return (
        '<!doctype html><html><body>'
        f'<script type="module">import * as THREE from "{import_from}"; '
        "const s = new THREE.Scene();</script></body></html>"
    )


def test_import_allowlist():
    validate_three_imports(three_html("three"))
    validate_three_imports(three_html("/vendor/three.module.js"))
    with pytest.raises(ValueError):
        validate_three_imports(three_html("https://cdn.example.com/three.js"))
    with pytest.raises(ValueError):
        validate_three_imports("<!doctype html><html><body>no imports</body></html>")


def test_preview_injects_and_replaces_import_map():
    html = (
        '<!doctype html><html><head>'
        '<script type="importmap">{"imports":{"three":"https://bad.example/three.js"}}</script>'
        '</head><body><script type="module">import * as THREE from "three";</script></body></html>'
    )
    out = build_preview_html(html)
    assert "/vendor/three.module.js" in out
    assert "https://bad.example" not in out
    assert out.count("importmap") == 1
    assert "Content-Security-Policy" in out


def test_3d_validation_accepts_three_import():
    html = three_html()
    assert validate_html(html, three_d=True) == html


def test_3d_validation_rejects_cdn_import():
    with pytest.raises(ValidationError):
        validate_html(three_html("https://cdn.example.com/three.js"), three_d=True)


def test_2d_rejects_three_import():
    with pytest.raises(ValidationError):
        validate_html(three_html(), mode="2d")


def test_hybrid_requires_three_import():
    plain = "<!doctype html><html><body><div>Kape</div></body></html>"
    with pytest.raises(ValidationError):
        validate_html(plain, mode="hybrid")


def test_system_prompt_toggles_three():
    provider = Provider()
    persona = get_persona("baseline")
    assert "Three.js" in provider.system_prompt(persona, True)
    assert "Three.js" not in provider.system_prompt(persona, False)
