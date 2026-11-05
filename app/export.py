"""Export a run as a self-contained review bundle (zip)."""

import html
import io
import json
import zipfile

from app import config
from app.modes import mode_label, normalize_mode
from app.three import build_export_html


def _tokens(value) -> str:
    n = int(value or 0)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def _cost(cost, source) -> str:
    if cost is None:
        return "—"
    body = f"${float(cost):.4f}" if float(cost) >= 0.0001 else "<$0.0001"
    return f"est. {body}" if source in ("estimated", "mixed") else body


def _run_mode(run: dict) -> str:
    return normalize_mode(run.get("mode") or ("3d" if run.get("three_d") else "2d"))


def _direction(result: dict) -> str:
    direction = result.get("direction") or {}
    parts = [direction.get("layout"), direction.get("camera"), direction.get("transition")]
    if not all(parts):
        return ""
    return " · ".join(part.replace("_", " ") for part in parts)


def _card(result: dict, three: bool) -> str:
    persona = result.get("persona") or {}
    name = html.escape(str(persona.get("name", "Agent")), quote=True)
    tagline = html.escape(str(persona.get("tagline", "")), quote=True)
    color = html.escape(str(persona.get("color", "#8b98a9")), quote=True)
    persona_id = html.escape(str(persona.get("id", "")), quote=True)
    direction = html.escape(_direction(result), quote=True)
    chars = f"{int(result.get('chars') or 0):,}"
    elapsed = f"{(result.get('elapsed_ms') or 0) / 1000:.1f}s"

    traits = result.get("traits") or {}
    style = result.get("style") or {}
    profile = ""
    kernel = ""
    if traits:
        profile = (
            f"O {traits.get('O')} · C {traits.get('C')} · E {traits.get('E')} · "
            f"A {traits.get('A')} · N {traits.get('N')} · T {result.get('temperature', '—')}"
        )
    if style:
        kernel = (
            f"{style.get('density', '')} · {style.get('type_sizes', '?')} sizes · "
            f"{style.get('colors', '?')} colors · {str(style.get('easing', '')).replace('_', ' ')}"
        )

    if result.get("ok"):
        if three:
            frame = (
                f'<iframe sandbox="allow-scripts allow-same-origin" '
                f'src="previews/{persona_id}.html" title="{name}" loading="lazy"></iframe>'
            )
        else:
            body = html.escape(str(result.get("html", "")), quote=True)
            frame = f'<iframe sandbox="allow-scripts" srcdoc="{body}" title="{name}"></iframe>'
        status = '<span class="ok">rendered</span>'
    else:
        frame = f'<div class="failed">{html.escape(str(result.get("error") or "no output"))}</div>'
        status = '<span class="bad">failed</span>'

    return f"""
    <article class="card" style="--accent:{color}">
      <header><h2>{name}</h2><span class="dot"></span></header>
      <p class="tagline">{tagline}</p>
      <div class="dir">{direction}</div>
      <div class="traits">{html.escape(profile)}</div>
      <div class="kernel">{html.escape(kernel)}</div>
      <div class="frame">{frame}</div>
      <footer><span>{status}</span><span>8s loop · 1080×1080 · {chars} chars · {elapsed}</span></footer>
    </article>"""


def _usage_rows(run: dict) -> str:
    rows = []
    for result in run.get("results") or []:
        persona = result.get("persona") or {}
        usage = result.get("usage") or {}
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(persona.get('name', 'Agent')))}</td>"
            f"<td class='n'>{_tokens(usage.get('prompt_tokens'))}</td>"
            f"<td class='n'>{_tokens(usage.get('completion_tokens'))}</td>"
            f"<td class='n'>{_tokens(usage.get('total_tokens'))}</td>"
            f"<td class='n'>{_cost(usage.get('cost_usd'), usage.get('cost_source'))}</td>"
            f"<td class='n'>{(result.get('elapsed_ms') or 0) / 1000:.1f}s</td>"
            f"<td class='n'>{int(result.get('chars') or 0):,}</td>"
            f"<td class='{'ok' if result.get('ok') else 'bad'}'>"
            f"{'rendered' if result.get('ok') else 'failed'}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def build_review_html(run: dict) -> str:
    mode = _run_mode(run)
    three = mode != "2d"
    total = run.get("usage_total") or {}
    brief = html.escape(str(run.get("brief", "")), quote=False)
    created = html.escape(str(run.get("created_at", ""))[:19].replace("T", " "))
    provider = html.escape(str(run.get("provider", "")))
    model = html.escape(str(run.get("model", "")))
    run_id = html.escape(str(run.get("run_id", "")))

    banner = (
        '<div class="banner">This bundle contains ES modules. Browsers block module '
        'imports from <code>file://</code>. Open a terminal in this folder, run '
        '<code>python -m http.server 8080</code>, then visit '
        '<code>http://127.0.0.1:8080/review.html</code>.</div>'
        if three else
        '<div class="banner quiet">This bundle is offline. Double-click to open; '
        'no server needed for 2D.</div>'
    )
    cards = "".join(_card(result, three) for result in run.get("results") or [])

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='22' fill='%23fafafa'/%3E%3Ccircle cx='34' cy='50' r='9' fill='%23e0574f'/%3E%3Ccircle cx='50' cy='50' r='9' fill='%23e0a72e'/%3E%3Ccircle cx='66' cy='50' r='9' fill='%234f8cff'/%3E%3C/svg%3E">
<title>Troupe — {run_id}</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: #09090b; color: #fafafa;
    font: 14px/1.5 ui-sans-serif, system-ui, "Segoe UI", Roboto, Arial, sans-serif;
  }}
  main {{ max-width: 1600px; margin: 0 auto; padding: 28px 24px 60px; }}
  header.top {{
    display: flex; align-items: baseline; justify-content: space-between;
    gap: 16px; flex-wrap: wrap; padding-bottom: 18px; border-bottom: 1px solid #27272a;
  }}
  .brand {{ font-size: 20px; font-weight: 800; letter-spacing: -.3px; }}
  .meta {{ color: #a1a1aa; font: 12px/1.5 ui-monospace, Consolas, monospace; }}
  .banner {{
    margin: 18px 0 0; padding: 10px 14px; border: 1px solid #3f3f46;
    border-radius: 8px; background: #18181b; color: #d4d4d8; font-size: 12px;
  }}
  .banner.quiet {{ color: #a1a1aa; }}
  .banner code {{ background: #27272a; padding: 1px 5px; border-radius: 4px; }}
  section {{ margin-top: 26px; }}
  h1 {{ font-size: 13px; letter-spacing: .12em; text-transform: uppercase; color: #a1a1aa; margin: 0 0 10px; }}
  .brief {{
    padding: 16px 18px; border: 1px solid #27272a; border-radius: 10px;
    background: #0c0c0f; font: 16px/1.6 ui-serif, Georgia, "Times New Roman", serif;
  }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }}
  .card {{
    border: 1px solid #27272a; border-radius: 12px; background: #0c0c0f;
    overflow: hidden; position: relative;
  }}
  .card::before {{ content: ""; position: absolute; inset: 0 0 auto 0; height: 3px; background: var(--accent); }}
  .card header {{ display: flex; align-items: center; justify-content: space-between; padding: 14px 14px 0; }}
  .card h2 {{ font-size: 14px; margin: 0; }}
  .dot {{ width: 8px; height: 8px; border-radius: 50%; background: var(--accent); }}
  .tagline {{ margin: 2px 14px 0; color: #a1a1aa; font-size: 11.5px; min-height: 30px; }}
  .dir {{ margin: 8px 14px 0; color: #71717a; font: 9.5px/1.4 ui-monospace, Consolas, monospace; letter-spacing: .04em; text-transform: uppercase; }}
  .traits {{ margin: 6px 14px 0; color: #a1a1aa; font: 9.5px/1.4 ui-monospace, Consolas, monospace; }}
  .kernel {{ margin: 1px 14px 0; color: #52525b; font: 9.5px/1.4 ui-monospace, Consolas, monospace; }}
  .frame {{ position: relative; margin: 12px; border-radius: 8px; overflow: hidden; background: #000; aspect-ratio: 1 / 1; border: 1px solid #27272a; }}
  .frame iframe {{ position: absolute; top: 0; left: 0; width: 1080px; height: 1080px; border: 0; transform-origin: top left; background: #000; }}
  .frame .failed {{ padding: 14px; color: #fca5a5; font: 11px/1.5 ui-monospace, Consolas, monospace; overflow-wrap: anywhere; }}
  .card footer {{ display: flex; justify-content: space-between; gap: 8px; padding: 0 14px 12px; color: #71717a; font-size: 10.5px; }}
  .ok {{ color: #4ade80; }}
  .bad {{ color: #f87171; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; }}
  th {{ text-align: left; color: #a1a1aa; font-weight: 600; padding: 7px 8px; border-bottom: 1px solid #27272a; }}
  td {{ padding: 7px 8px; border-bottom: 1px solid #1f1f23; color: #d4d4d8; }}
  td.n, th.n {{ text-align: right; font-variant-numeric: tabular-nums; }}
</style>
</head>
<body>
<main>
  <header class="top">
    <div class="brand">◐ Troupe</div>
    <div class="meta">{run_id} · {mode_label(mode)} · {provider}/{model} · {created} ·
      {_tokens(total.get('prompt_tokens'))} in / {_tokens(total.get('completion_tokens'))} out ·
      {_cost(total.get('cost_usd'), total.get('cost_source'))}</div>
  </header>
  {banner}
  <section>
    <h1>The brief</h1>
    <div class="brief">{brief}</div>
  </section>
  <section>
    <h1>The room</h1>
    <div class="grid">{cards}
    </div>
  </section>
  <section>
    <h1>Usage</h1>
    <table>
      <thead><tr><th>Agent</th><th class="n">In</th><th class="n">Out</th><th class="n">Total</th>
      <th class="n">Cost</th><th class="n">Time</th><th class="n">Chars</th><th>Status</th></tr></thead>
      <tbody>{_usage_rows(run)}</tbody>
    </table>
  </section>
</main>
<script>
  function fit() {{
    document.querySelectorAll(".frame").forEach(function (wrap) {{
      var iframe = wrap.querySelector("iframe");
      if (!iframe) return;
      iframe.style.transform = "scale(" + (wrap.clientWidth / 1080) + ")";
    }});
  }}
  addEventListener("resize", fit);
  addEventListener("load", fit);
  fit();
</script>
</body>
</html>
"""


def _readme(run: dict, three: bool) -> str:
    lines = [
        "Troupe — run export",
        "",
        f"Run:      {run.get('run_id')}",
        f"Created:  {run.get('created_at')}",
        f"Mode:     {mode_label(_run_mode(run))}",
        f"Provider: {run.get('provider')} / {run.get('model')}",
        "",
        "Contents",
        "  review.html      the review page (brief, previews, usage)",
        "  run.json         the full run record",
        "  previews/        each agent's self-contained HTML",
    ]
    if three:
        lines.append("  vendor/          Three.js r160")
    lines += ["", "How to open"]
    if three:
        lines += [
            "  3D/Hybrid uses ES modules, which browsers block from file://.",
            "  Open a terminal in this folder and run:",
            "      python -m http.server 8080",
            "  then open http://127.0.0.1:8080/review.html",
        ]
    else:
        lines.append("  Double-click review.html. No server needed.")
    return "\n".join(lines) + "\n"


def build_export(run: dict) -> bytes:
    """Return a zip with the review page, the raw run, and every preview."""
    mode = _run_mode(run)
    three = mode != "2d"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("run.json", json.dumps(run, ensure_ascii=False, indent=2))
        archive.writestr("review.html", build_review_html(run))
        archive.writestr("README.txt", _readme(run, three))
        for result in run.get("results") or []:
            if not result.get("ok"):
                continue
            persona_id = result["persona"]["id"]
            body = result.get("html", "")
            archive.writestr(
                f"previews/{persona_id}.html",
                build_export_html(body) if three else body,
            )
        if three:
            vendor = config.ROOT / "app" / "vendor"
            archive.write(vendor / "three.module.js", "vendor/three.module.js")
            archive.write(vendor / "three.LICENSE", "vendor/three.LICENSE")
    return buffer.getvalue()
