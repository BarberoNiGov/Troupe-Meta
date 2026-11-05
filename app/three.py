"""Three.js preview support: vendored r160, import map, CSP, import allowlist."""

import re

THREE_VERSION = "160"

THREE_PROMPT = """3D MODE IS ON.

Build this reveal as a real WebGL scene with Three.js r160.

Hard rules:
- Import Three.js exactly once with: import * as THREE from "three";
  The import map is provided by the preview server. Do NOT write your own import map.
- Only core Three.js. No addons, loaders, GLTF, OrbitControls, post-processing,
  external fonts, external textures, or network requests.
- Create one WebGLRenderer with a 1080x1080 canvas, antialias true,
  setPixelRatio(1), and a dark or branded background.
- Use a PerspectiveCamera or OrthographicCamera, and 2-3 lights maximum.
- Procedural geometry only: Box, Sphere, Torus, Cylinder, Cone, Ring, Plane,
  Shape, Extrude, Lathe, or custom BufferGeometry.
- No shadows. Keep the scene under 60 meshes. Dispose geometries and materials.
- Animate with requestAnimationFrame and THREE.Clock. Make an exact 8-second loop.
- In pure 3D, the wordmark should be 3D geometry inside the scene. Avoid a large
  2D overlay; a small tagline or caption is enough.
- The brand name must be legible for at least 5 of the 8 seconds.
- If post-processing is unavailable, fake glow with sprites, rings, or layered planes.
- Keep the file under 180 KB.

The persona still decides the style. This is a shared capability, not a house style.
"""

HYBRID_PROMPT = """HYBRID MODE: 3D WORLD + 2D OVERLAY.

This is not "3D with a label." Split the responsibilities:

3D layer (Three.js):
- Depth, hero geometry, camera move, lighting, particles, atmosphere.
- A real WebGLRenderer at 1080x1080.
- Keep the scene under 60 meshes and 2-3 lights; no shadows; dispose.

2D layer (HTML/CSS over the canvas):
- The wordmark, tagline, labels, grain, vignette, scanlines, and 2D transitions.
- Use real HTML text for crisp typography, not a texture of text.
- CSS keyframes on the same 8-second beat sheet.

Composition:
- Canvas full-bleed; overlay position:absolute; inset:0; pointer-events:none.
- The 2D wordmark should remain legible for at least 5 of the 8 seconds.
- The 3D and 2D layers must loop to the same opening pose.
- The 2D transition can mask/wipe/reveal the 3D scene.
- Do not put the wordmark in the 3D scene except as a secondary element.

Keep the file under 180 KB.
"""

IMPORT_MAP = '<script type="importmap">{"imports":{"three":"/vendor/three.module.js"}}</script>'
PREVIEW_CSP = (
    "default-src 'none'; script-src 'self' 'unsafe-inline'; "
    "style-src 'unsafe-inline'; img-src data:; font-src data:; "
    "connect-src 'none';"
)
FRAME_ANCESTORS = "frame-ancestors http://127.0.0.1:8030 http://localhost:8030;"

_ALLOWED_SPECIFIERS = {"three", "/vendor/three.module.js"}
_STATIC_IMPORT = re.compile(
    r"\bimport\s+(?:[^;\n]*?\s+from\s+)?[\"']([^\"']+)[\"']", re.I
)
_DYNAMIC_IMPORT = re.compile(r"\bimport\s*\(\s*[\"']([^\"']+)[\"']", re.I)
_CSP_META = re.compile(
    r"<meta[^>]+http-equiv=[\"']?Content-Security-Policy[\"']?[^>]*>", re.I
)
_IMPORT_MAP_TAG = re.compile(
    r"<script[^>]*type=[\"']importmap[\"'][^>]*>.*?</script>", re.I | re.S
)


def validate_three_imports(html: str) -> None:
    specs = _STATIC_IMPORT.findall(html) + _DYNAMIC_IMPORT.findall(html)
    if not specs:
        raise ValueError("3D mode requires import * as THREE from \"three\"")
    for spec in specs:
        if spec not in _ALLOWED_SPECIFIERS:
            raise ValueError(f"3D import not allowed: {spec!r}")
    if not any(spec in _ALLOWED_SPECIFIERS for spec in specs):
        raise ValueError("3D mode requires a Three.js import")


def build_preview_html(html: str) -> str:
    """Inject the preview CSP + import map, replacing any the model wrote."""
    html = _CSP_META.sub("", html)
    html = _IMPORT_MAP_TAG.sub("", html)
    inject = (
        f'<meta http-equiv="Content-Security-Policy" content="{PREVIEW_CSP}">'
        f"{IMPORT_MAP}"
    )
    head = re.search(r"<head[^>]*>", html, re.I)
    if head:
        return html[: head.end()] + inject + html[head.end():]
    html_tag = re.search(r"<html[^>]*>", html, re.I)
    if html_tag:
        return html[: html_tag.end()] + "<head>" + inject + "</head>" + html[html_tag.end():]
    return "<head>" + inject + "</head>" + html


def build_export_html(html: str) -> str:
    """Preview HTML for an offline bundle; `vendor/` sits beside `previews/`."""
    return build_preview_html(html).replace(
        '{"imports":{"three":"/vendor/three.module.js"}}',
        '{"imports":{"three":"../vendor/three.module.js"}}',
    )
