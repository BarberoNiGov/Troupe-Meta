# Demo runbook

## Before recording

```powershell
cd C:\Coding Projects\Troupe
python scripts/serve.py
```

This starts the studio on **8030** and the 3D preview origin on **8031**. Open <http://127.0.0.1:8030>. Confirm:

- the provider badge shows **muse-spark** for the final recording;
- the medium selector is on **Hybrid** for the polished take, or **2D** / **3D** for the A/B;
- eight previews are visible (or press **Run the room**);
- **Export** is visible in the top bar;
- the usage table shows tokens; no console errors;
- if 3D or Hybrid cards are blank, the preview server on 8031 is not running.

If the page is empty, press **Run the room** once. It takes about **90–120 seconds** for eight agents on Muse Spark.

**Freeze a run for the recording.** After the final run, copy its id from `/latest` or the run metadata, then open `http://127.0.0.1:8030/?run=<run_id>`. That keeps the screenshots and video on the same run even if you experiment afterward.

## Script (final cut: 1:17)

1. **Frame the experiment.** "A roster of eleven coding agents, eight in the room, one brief. The question is whether persona changes the output."
2. **Show the brief and the cast.** *"An 8-second animated logo reveal for Kape, a Filipino coffee brand."* Point at the cast picker: eight core agents, three flavor swap-ins.
3. **Walk the row.** Baseline, Anxious Perfectionist, Chaotic Experimentalist, Stoic Minimalist, Hype Maximalist, Accessibility Advocate, Deadpan Engineer, Romantic Storyteller. "Each agent carries a Big Five-inspired record and a design kernel. The model writes the HTML. Code owns the contract: offline, self-contained, 1080×1080, 8-second loop."
   - The kernel is visible in the output: the Deadpan agent animates only opacity and transform; the Stoic file is ~2 KB; the Hype agent fills the frame.
   - Every card declares **layout · camera · transition**. The direction grammar is always on for all three modes.
   - **2D** is the default: CSS/SVG/canvas only, the diversity winner.
   - **3D** uses the vendored Three.js library, with the wordmark as 3D geometry.
   - **Hybrid** uses a 3D world with a crisp HTML/CSS wordmark and overlay: the legibility winner.
   - The mode selector is the medium A/B; the grammar stays constant.
4. **Show the usage table.** "Tokens are exact per agent. Cost is provider-reported on OpenRouter, or estimated when prices are configured. This is the monitor, not part of the vote."
5. **Toggle Blind vote.** Identities disappear, order shuffles, colours neutralize, preview links hide, usage labels become A–H. "This is the actual measurement. The audience picks the strongest motion without knowing which persona made it."
6. **Vote.** Pick one. Then **Reveal**. The winner is highlighted, votes appear, and the usage table maps back to names.
7. **Show the analysis.** `python scripts/analyze.py`: 2D visual similarity **0.46**, 3D **0.59**, Hybrid **0.62**; all three are 8/8 with 0 errors. "2D is the diversity winner, Hybrid is the most legible — real HTML type over a 3D world — and also the most homogeneous. The model moved diversity more than any prompt change: the same cast scored 0.62 / 0.65 / 0.72 on the development model."
8. **Export the run.** Press **Export**. "One zip: the review page, the full run record, every preview, and the vendored library. 2D opens offline by double-click. 3D needs `python -m http.server` because browsers block modules from `file://`." Open `review.html`: all eight previews, each with its **OCEAN profile and kernel**, plus the usage table.
9. **Be honest.** "This is a pilot. One brief, one model, a handful of runs. The result is a style effect, not proof of higher quality. The baseline is in the room; if personality helps, a persona should beat it."
10. **Close.** "Troupe: a writers' room for coding agents."

## Provider

The submission runs on **Muse Spark 1.3 Contributor** through OpenRouter:

```dotenv
# .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=meta/muse-spark-1.3-contributor
LLM_TIMEOUT_SECONDS=600
LLM_MAX_TOKENS=48000
```

The Contributor tier requires **paid model training** enabled in OpenRouter (Settings → Privacy). If that setting is off, the endpoint returns `404 … Paid model training violation`; the standard tier `meta/muse-spark-1.3` works without it at 12.5× the price.

Restart the server, then verify:

```powershell
python scripts/spike.py --mode 2d
```

The badge must read `muse-spark / meta/muse-spark-1.3-contributor` before recording. If the provider rejects `response_format`, the client retries without it automatically. OpenRouter reports cost directly, so the usage table shows dollars. Muse Spark takes **36–71s per agent**; `LLM_TIMEOUT_SECONDS=600` covers it, and `LLM_MAX_TOKENS=48000` removes the 8k truncation we hit once.

## Submission checklist

- [ ] Public repository, no `.env`
- [ ] `README.md`, `HACKATHON.md`, `LICENSE`
- [ ] `app/vendor/three.module.js` and `app/vendor/three.LICENSE` included
- [ ] Screenshots (2D, 3D, hybrid, mobile)
- [x] Final narrated `docs/demo.mp4` (1:17, Muse Spark)
- [ ] Narrated video recorded with the Muse Spark badge visible
- [ ] No `data/runs/` or `.env` committed
- [ ] Rotate any development API keys used before the submission
- [ ] Submit before **Nov 4, 9:00 PM ET / Nov 5, 10:00 AM PHT**

## If something fails

| Symptom | Recovery |
|---|---|
| Empty studio | Press **Run the room**; a run takes **90–120s** for eight agents on Muse Spark. |
| `404` "Paid model training" | The Contributor tier needs training enabled in OpenRouter → Settings → Privacy, or switch to `meta/muse-spark-1.3`. |
| One card timed out | `LLM_TIMEOUT_SECONDS=600` must be set; Muse Spark takes 36–71s per agent. |
| `output truncated at 48000 tokens` | The file exceeds the validator cap anyway; ask for a smaller output or accept the failure. |
| One card failed | Keep going; the UI isolates the failure. The validator rejected an unsafe or malformed output. |
| Provider error | Check the key and `LLM_PROVIDER`; run `python scripts/spike.py` in the terminal for the exact error. |
| Preview blank | Wait for the 8s loop; some personas hold negative space early. Click **open full**. For 3D/Hybrid, verify the preview server on 8031. |
| No Muse Spark key | Record on the standard tier (`meta/muse-spark-1.3`) as a fallback. |
| Export does nothing | A run must be loaded. Press **Run the room** or open `?run=<id>`; the button hides until then. |
