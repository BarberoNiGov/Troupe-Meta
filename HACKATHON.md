# Hackathon notes

**Event:** Meta Global AI Developer Hackathon — November 3–4, 2026
**Track:** Solo / indie
**Project:** Troupe — persona-conditioned coding agents for motion graphics

## What was built during the event

Everything in this repository was written during the hackathon window:

- `app/personas.py` — eleven temperaments, an eight-agent default cast, Big Five-inspired trait records with design kernels, derived temperature, and the shared HTML output contract
- `app/providers/` — OpenRouter/Muse Spark and Meta/Muse Spark adapters
- `app/usage.py` — token normalization, provider-reported cost, configurable estimates, totals
- `app/cinema.py` — shared layout/camera/transition grammar, beat sheet, persona direction biases
- `app/modes.py` — 2D, 3D, and hybrid medium modes
- `app/three.py` — vendored Three.js prompt, hybrid prompt, import allowlist, import map, preview CSP
- `app/preview.py` — isolated preview origin for generated 3D HTML and Three.js
- `app/validate.py` — strict HTML validation, direction validation, network blocking, CSP injection
- `app/generate.py` — parallel generation with concurrency limits, per-agent error isolation, run persistence
- `app/main.py` — FastAPI routes
- `app/export.py` — self-contained zip export: review page, run record, previews, and the vendored library
- `app/static/` — studio UI with cast picker, 2D/3D/Hybrid selector, export, direction metadata, usage table, sandboxed previews, and blind voting
- `scripts/serve.py` — starts the studio and the isolated preview origin
- `scripts/spike.py` — one-shot cast run with token/cost output
- `scripts/render_check.py` — Playwright render, WebGL, and console-error checks
- `scripts/analyze.py` — visual/palette diversity and usage tables
- `tests/` — offline validation, persona, cinema/direction, usage, 3D, export, and API tests

No code was copied from another project. The repository is MIT-licensed and must be published publicly before submission.

## What is original

- The controlled comparison of persona-conditioned coding agents on a single motion-graphics brief.
- The strict output contract: every agent must produce an offline, self-contained HTML file that passes the same validator.
- The sandboxing model: generated code never gets network access and never touches the parent page.
- The blind-vote mode: identities, order, colours, and preview URLs are hidden until reveal.
- The cast system: an eleven-agent roster, an eight-agent controlled comparison, and three flavor swap-ins.
- The shared 3D capability: vendored Three.js r160, a strict import allowlist, a separate preview origin, and a CSP that keeps generated code offline.
- The hybrid medium: a 3D world with a deliberate 2D HTML/CSS wordmark and overlay, so typography stays crisp while the scene keeps depth.
- The 2D/3D/Hybrid mode selector and the measured trade-off: 2D is the diversity winner, hybrid is the legibility winner, pure 3D sits between them.
- The always-on direction grammar: layout, camera, and transition declared by every agent and validated by code, with a persona bias for each axis.
- The run export: one zip with a standalone review page, the full run record, every preview, and the vendored Three.js, with the 3D import map rewritten so the bundle is self-contained.
- The personality record: each agent's traits and design kernel are structured data, the prompt is generated from them, and sampling temperature is derived from the record rather than hand-set. The honest finding is that explicit kernels raise adherence and reduce 2D diversity.
- The per-agent token/cost monitor and the visual/palette diversity analysis.
- The best-of-eight vs. neutral baseline comparison, the 2D-vs-3D trade-off, and the grammar's effect on 3D homogenization.

## Provider status

The submission runs **Muse Spark 1.3 Contributor** through OpenRouter (`meta/muse-spark-1.3-contributor`), which routes to Meta. The direct Meta Model API (`muse-spark-1.3`) is also supported. Switching routes changes only `LLM_PROVIDER`; the prompts, validator, and UI are shared.

## Safety and scope

- No political, medical, or harmful content.
- 2D previews are sandboxed with `allow-scripts` only. 3D previews run on a separate preview origin with `allow-same-origin` scoped to that origin; they cannot reach the studio.
- Every preview has a CSP that blocks network requests. External URLs, external scripts, storage, dialogs, and navigation are rejected by the validator.
- 3D imports are limited to the vendored Three.js module.
- Exports are generated locally from the run record; nothing is uploaded.
