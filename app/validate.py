"""Provider contract and strict HTML validation."""

import re

from app import config
from app.cinema import validate_direction
from app.modes import is_3d, normalize_mode
from app.three import validate_three_imports


class ValidationError(ValueError):
    pass


_EXTERNAL_URL = re.compile(r"https?://[^\s\"'<>]+", re.I)
_ALLOWED_URL_PREFIXES = ("http://www.w3.org/", "https://www.w3.org/")
_FORBIDDEN = [
    (re.compile(r"<script[^>]+src\s*=", re.I), "external script"),
    (re.compile(r"<link[^>]+href\s*=", re.I), "external stylesheet"),
    (re.compile(r"@import", re.I), "CSS @import"),
    (re.compile(r"\bfetch\s*\(", re.I), "fetch"),
    (re.compile(r"XMLHttpRequest", re.I), "XMLHttpRequest"),
    (re.compile(r"\bWebSocket\b", re.I), "WebSocket"),
    (re.compile(r"localStorage|sessionStorage|indexedDB", re.I), "storage"),
    (re.compile(r"document\.cookie", re.I), "cookie access"),
    (re.compile(r"\b(alert|confirm|prompt)\s*\(", re.I), "blocking dialog"),
    (re.compile(r"window\.location|location\.href|window\.open", re.I), "navigation"),
    (re.compile(r"\beval\s*\(", re.I), "eval"),
]

CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
    "img-src data:; font-src data:; media-src data:; connect-src 'none';"
)


def validate_html(raw: str, three_d: bool = False, mode: str | None = None) -> str:
    try:
        mode = normalize_mode(mode, three_d)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    html = (raw or "").strip()
    if not html:
        raise ValidationError("empty html")
    if len(html.encode("utf-8")) > config.MAX_HTML_BYTES:
        raise ValidationError(f"html exceeds {config.MAX_HTML_BYTES} bytes")
    low = html.lower()
    if "<!doctype html" not in low or "<html" not in low or "</html>" not in low:
        raise ValidationError("not a complete HTML document")
    for match in _EXTERNAL_URL.findall(html):
        if not match.lower().startswith(_ALLOWED_URL_PREFIXES):
            raise ValidationError(f"external URL not allowed: {match[:80]}")
    for pattern, label in _FORBIDDEN:
        if pattern.search(html):
            raise ValidationError(f"forbidden: {label}")
    if is_3d(mode):
        try:
            validate_three_imports(html)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        # The preview server injects the 3D CSP and import map.
        return html
    if re.search(r"\bimport\s+(?:[^;\n]*?\s+from\s+)?[\"']three[\"']", html, re.I) or \
            re.search(r"\bimport\s*\(\s*[\"']three[\"']", html, re.I):
        raise ValidationError("Three.js import is not allowed in 2D mode")
    return inject_csp(html)


def inject_csp(html: str) -> str:
    meta = f'<meta http-equiv="Content-Security-Policy" content="{CSP}">'
    head = re.search(r"<head[^>]*>", html, re.I)
    if head:
        return html[: head.end()] + meta + html[head.end():]
    html_tag = re.search(r"<html[^>]*>", html, re.I)
    if html_tag:
        return html[: html_tag.end()] + "<head>" + meta + "</head>" + html[html_tag.end():]
    return "<head>" + meta + "</head>" + html


def validate_generation(data: dict, three_d: bool = False, mode: str | None = None) -> tuple[str, str, dict]:
    if not isinstance(data, dict):
        raise ValidationError("model did not return a JSON object")
    try:
        mode = normalize_mode(mode, three_d)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    approach = str(data.get("approach", "")).strip()
    html = str(data.get("html", "")).strip()
    if not approach:
        raise ValidationError("missing approach")
    if not html:
        raise ValidationError("missing html")
    try:
        direction = validate_direction(data)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    return approach[:600], validate_html(html, mode=mode), direction
