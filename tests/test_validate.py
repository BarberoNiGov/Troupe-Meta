from app.validate import ValidationError, inject_csp, validate_generation, validate_html

GOOD = """<!doctype html>
<html><head><title>x</title><style>body{background:#000} @keyframes a{to{opacity:0}}</style></head>
<body><div style="animation:a 8s infinite">Kape</div></body></html>"""


def test_good_html_passes():
    html = validate_html(GOOD)
    assert "Content-Security-Policy" in html
    assert "<!doctype html>" in html.lower()


def test_external_script_rejected():
    try:
        validate_html('<!doctype html><html><body><script src="https://x.com/a.js"></script></body></html>')
    except ValidationError as exc:
        assert "external" in str(exc).lower() or "forbidden" in str(exc).lower()
    else:
        raise AssertionError("should reject external script")


def test_external_url_rejected():
    try:
        validate_html('<!doctype html><html><body style="background:url(https://x.com/a.png)"></body></html>')
    except ValidationError as exc:
        assert "external" in str(exc).lower()
    else:
        raise AssertionError("should reject external URL")


def test_svg_namespace_allowed():
    html = '<!doctype html><html><body><svg xmlns="http://www.w3.org/2000/svg"><circle r="5"/></svg></body></html>'
    assert "svg" in validate_html(html)


def test_missing_doctype_rejected():
    try:
        validate_html("<html><body>hi</body></html>")
    except ValidationError:
        pass
    else:
        raise AssertionError("should reject incomplete document")


def test_validate_generation():
    approach, html, direction = validate_generation({
        "approach": "calm plan",
        "layout": "centered_hero",
        "camera": "static",
        "transition": "hard_cut",
        "html": GOOD,
    })
    assert approach == "calm plan"
    assert "Content-Security-Policy" in html
    assert direction == {"layout": "centered_hero", "camera": "static", "transition": "hard_cut"}


def test_validate_generation_requires_direction():
    try:
        validate_generation({"approach": "calm plan", "html": GOOD})
    except ValidationError:
        pass
    else:
        raise AssertionError("missing direction must fail")


def test_validate_generation_rejects_invalid_direction():
    try:
        validate_generation({
            "approach": "calm plan",
            "layout": "orbit_stage",
            "camera": "teleport",
            "transition": "hard_cut",
            "html": GOOD,
        })
    except ValidationError:
        pass
    else:
        raise AssertionError("invalid camera must fail")


def test_csp_injected_after_head():
    html = inject_csp("<html><head><style></style></head><body></body></html>")
    assert html.index("Content-Security-Policy") < html.index("<style>")
