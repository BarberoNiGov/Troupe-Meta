# Submission plan

**Event:** Meta Global AI Developer Hackathon — deadline **Nov 5, 2026, 10:00 AM GMT+8**
**Project:** Troupe — persona-conditioned coding agents for motion graphics
**Track:** Indie Developer Track
**Problem statement:** Build for Your World — motion design's first-hour problem is convergence: every concept starts from the same references. Troupe returns eight genuinely different, renderable directions in about 90 seconds, then scores them blind.
**Model:** Muse Spark 1.3 Contributor (`meta/muse-spark-1.3-contributor`), served through OpenRouter; provider reported by OpenRouter is **Meta**.

The route is OpenRouter, but the model is Meta's. That is stated in the project description, the README, and `HACKATHON.md`. The repository contains one model provider family: Muse Spark, through OpenRouter and the direct Meta Model API.

## 1. Freeze the run for the video

Use the analyzed Muse Spark runs, not `/latest`:

| Mode | Run id |
|---|---|
| 2D | `20261104-232311-256b` |
| 3D | `20261104-232600-432d` |
| Hybrid (hero) | `20261104-233122-d349` |

```text
http://127.0.0.1:8030/?run=20261104-233122-d349
```

Results: 8/8 in every mode, 0 render errors. Visual similarity **0.46 / 0.59 / 0.62**; palette **0.00 / 0.01 / 0.03**. Costs **$0.0093 / $0.0110 / $0.0117** per run. 56 tests pass.

## 2. Final video (1:17, AI Studio voiceover)

**Done:** `docs/demo.mp4` — 1920×1080, H.264 + AAC, 13 MB, 77.4 s. The AI Studio voiceover was 1:17, so the screen take was re-timed to it rather than padded with silence.

| Time | Visual |
|---|---|
| 0:00–0:05 | The room, all 8 cards, Muse Spark badge |
| 0:05–0:16 | Brief + cast pills |
| 0:16–0:33 | Cards, approach text and previews |
| 0:33–0:48 | Hybrid selector, second row |
| 0:48–0:56 | Usage table with real costs |
| 0:56–1:04 | Blind vote → reveal |
| 1:04–1:12 | Revealed room, winner |
| 1:12–1:17 | Export click, close |

The narration (for reference; the audio is already generated):

1. "Eleven coding agents. Eight in the room. One brief. And no consensus."
2. "This is Troupe. Eight agents, each with a different personality, independently write a self-contained HTML motion graphic. Same brief. Same rules. Different temperament."
3. "Each agent carries a Big Five-inspired record and a design kernel. The Deadpan Engineer gets two type sizes and only animates opacity. The Hype Maximalist gets five sizes and spring overshoot. The prompt is generated from that record."
4. "Every output is validated by code: offline, 1080 by 1080, an eight-second loop. The direction grammar is always on — layout, camera, transition — and the code checks it."
5. "The same cast works in 2D, real Three.js 3D, or Hybrid. Tokens are exact per agent. On Muse Spark, a full eight-agent run costs about one cent."
6. "Then the room goes blind. Names, colors, order, links — all hidden. The audience votes on the motion, not the persona."
7. "The result is honest: 8/8 in every mode, zero render errors. 2D is the most diverse. Hybrid is the most legible, and the most homogeneous."
8. "Every run exports as one zip: the review page, the run record, every preview, and the library. Troupe — a writers' room for coding agents."

## 3. Publish the repository

`gh` is not installed, so use the GitHub web UI.

```powershell
cd "C:\Coding Projects\Troupe"
git init -b main
git add .
git status          # .env, .venv, data/runs, __pycache__ must be absent
git commit -m "Troupe: persona-conditioned coding agents for motion graphics"
```

Then: **GitHub → New repository → `troupe` → Public → no README** →

```powershell
git remote add origin https://github.com/<you>/troupe.git
git push -u origin main
```

Before pushing:

- `app/vendor/three.module.js` and `three.LICENSE` included.
- `docs/demo.mp4` is the final Muse Spark recording.
- `README.md`, `HACKATHON.md`, `LICENSE`, `docs/SUBMISSION.md` included.
- `git grep -n "sk-or-"` returns nothing.
- `.env` is not tracked.

## 4. Post on X (Most Viral Track)

> Eleven AI agents. Eight in the room. One brief. No consensus.
>
> Troupe: persona-conditioned coding agents that each make a motion graphic from the same brief, then get scored blind.
>
> Muse Spark 1.3 · 8/8 · 0 errors · ~$0.01/run
>
> [repo link] [video]
> #MetaHackathon

Attach a 20–30 second clip, not the full video. Paste the post URL into the **Most Viral Track** field.

## 5. Submission form

| Field | Answer |
|---|---|
| Team name | **Troupe** |
| Team members | Jonrich Bascug, RichJ |
| Track | **Indie Developer Track** |
| Problem statement | **Build for Your World** |
| Most Viral Track | X post URL |
| Project description | below |

> Motion design has a first-hour problem: every concept starts from the same references, so the directions converge. Troupe is a studio where a cast of persona-conditioned coding agents independently build a motion graphic from the same brief — eight genuinely different, renderable directions in about 90 seconds — then get scored blind.
>
> Eight agents each carry a Big Five-inspired record and a design kernel — type scale, color budget, easing, risk, and what they refuse to do. The prompt and sampling temperature are derived from that record. A code-owned direction grammar forces every agent to declare a layout, camera, and transition, and validates it. Outputs are self-contained HTML, sandboxed, offline, 1080×1080, eight-second loops.
>
> On Muse Spark 1.3, the core cast generated 8/8 in 2D, 3D, and Hybrid with zero render errors. The experiment reports the trade-off honestly: 2D is the most diverse (0.46 visual similarity), Hybrid is the most legible and the most homogeneous (0.62). A full eight-agent run costs about $0.01. Every run exports as a self-contained zip with a review page, the run record, every preview, and the vendored Three.js.
>
> Built solo during the hackathon. Muse Spark 1.3 Contributor, served through OpenRouter (provider: Meta).

## 6. Order and clock

1. Record the video (~40 min).
2. Commit and push the repo (~15 min), after the video exists.
3. Post on X (~10 min).
4. Submit the form (~10 min).
5. Submit by **9:30 AM GMT+8**, not 10:00.

After submitting: rotate any development API key that was exposed before the submission.
