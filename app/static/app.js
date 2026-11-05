/* Troupe studio: cast, run, usage monitor, sandboxed previews, blind voting. */

const state = {
  config: null,
  personas: [],
  selectedIds: [],
  maxCast: 8,
  mode: "2d",
  run: null,
  running: false,
  cardData: {},
  blind: false,
  revealed: false,
  blindOrder: null,
  votes: {},
  myVote: null,
};

const $ = (id) => document.getElementById(id);

function shuffle(values) {
  const out = [...values];
  for (let i = out.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

function personaById(id) {
  return state.personas.find((p) => p.id === id);
}

function selectedPersonas() {
  return state.selectedIds.map(personaById).filter(Boolean);
}

function numberWord(n) {
  return {
    3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
    8: "eight", 9: "nine", 10: "ten", 11: "eleven",
  }[n] || String(n);
}

function fmtTokens(value) {
  const n = Number(value) || 0;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

function fmtCost(cost, source) {
  if (cost === null || cost === undefined || Number.isNaN(Number(cost))) return "—";
  const n = Number(cost);
  let body;
  if (n === 0) body = "$0.0000";
  else if (n < 0.0001) body = "<$0.0001";
  else body = `$${n.toFixed(4)}`;
  return source === "estimated" || source === "mixed" ? `est. ${body}` : body;
}

function usageSummary(run) {
  const u = run && run.usage_total;
  if (!u) return "";
  return `${fmtTokens(u.prompt_tokens)} in / ${fmtTokens(u.completion_tokens)} out · ${fmtCost(u.cost_usd, u.cost_source)}`;
}

function usageLine(result) {
  const u = result.usage || {};
  const secs = (result.elapsed_ms / 1000).toFixed(1);
  if (!u.total_tokens) return `${secs}s · ${(result.chars || 0).toLocaleString()} chars`;
  return `${fmtTokens(u.prompt_tokens)} in · ${fmtTokens(u.completion_tokens)} out · ${fmtCost(u.cost_usd, u.cost_source)} · ${secs}s`;
}

function personaCard(persona) {
  const card = document.createElement("article");
  card.className = "card";
  card.dataset.persona = persona.id;
  card.style.setProperty("--persona-color", persona.color);

  const head = document.createElement("div");
  head.className = "card-head";
  const name = document.createElement("div");
  name.className = "card-name";
  const tagline = document.createElement("div");
  tagline.className = "card-tagline";
  head.append(name, tagline);

  const approach = document.createElement("div");
  approach.className = "approach empty";

  const direction = document.createElement("div");
  direction.className = "direction";

  const preview = document.createElement("div");
  preview.className = "preview-wrap";
  const skeleton = document.createElement("div");
  skeleton.className = "preview-skeleton idle";
  skeleton.textContent = "no output yet";
  const iframe = document.createElement("iframe");
  iframe.setAttribute("sandbox", "allow-scripts");
  iframe.setAttribute("referrerpolicy", "no-referrer");
  iframe.title = `${persona.name} preview`;
  iframe.hidden = true;
  preview.append(iframe, skeleton);

  const foot = document.createElement("div");
  foot.className = "card-foot";
  const status = document.createElement("span");
  status.className = "status";
  status.textContent = "idle";
  const right = document.createElement("span");
  right.className = "card-actions";
  const vote = document.createElement("button");
  vote.type = "button";
  vote.className = "vote-btn";
  vote.textContent = "Vote";
  vote.hidden = true;
  vote.addEventListener("click", () => castVote(persona.id));
  const open = document.createElement("a");
  open.className = "open-link";
  open.textContent = "open full ↗";
  open.target = "_blank";
  open.rel = "noopener noreferrer";
  open.hidden = true;
  const count = document.createElement("span");
  count.className = "vote-count";
  const meta = document.createElement("span");
  meta.className = "meta";
  right.append(vote, open, count, meta);
  foot.append(status, right);

  card.append(head, approach, direction, preview, foot);
  return card;
}

function updateTagline() {
  $("tagline").textContent = `${numberWord(state.selectedIds.length)} agents. one brief. no consensus.`;
}

function setMode(mode) {
  if (!["2d", "3d", "hybrid"].includes(mode)) mode = "2d";
  const changed = state.mode !== mode;
  state.mode = mode;
  document.querySelectorAll(".mode-btn").forEach((button) => {
    const active = button.dataset.mode === mode;
    button.classList.toggle("selected", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
  if (changed && state.run && modeOf(state.run) !== mode) {
    $("runMeta").textContent = "mode changed · run the room";
  }
}

function modeOf(run) {
  return (run && (run.mode || (run.three_d ? "3d" : "2d"))) || "2d";
}

function modeLabel(mode) {
  return { "2d": "2D", "3d": "3D", hybrid: "Hybrid" }[mode] || mode;
}

function buildCast() {
  const wrap = $("cast");
  wrap.replaceChildren();
  let flavorStarted = false;
  for (const persona of state.personas) {
    if (persona.pack === "flavor" && !flavorStarted) {
      flavorStarted = true;
      const sep = document.createElement("span");
      sep.className = "cast-sep";
      sep.textContent = "Flavor pack";
      wrap.append(sep);
    }
    const button = document.createElement("button");
    button.type = "button";
    button.className = `cast-pill${state.selectedIds.includes(persona.id) ? " selected" : ""}`;
    button.dataset.id = persona.id;
    button.style.setProperty("--persona-color", persona.color);
    const dot = document.createElement("span");
    dot.className = "dot";
    const label = document.createElement("span");
    label.textContent = persona.name;
    button.append(dot, label);
    button.addEventListener("click", () => toggleCast(persona.id));
    wrap.append(button);
  }
}

function toggleCast(id) {
  if (state.selectedIds.includes(id)) {
    if (state.selectedIds.length <= 3) {
      toast("Keep at least 3 agents in the room.");
      return;
    }
    state.selectedIds = state.selectedIds.filter((x) => x !== id);
  } else {
    if (state.selectedIds.length >= state.maxCast) {
      toast(`Max ${state.maxCast} for a blind run. Deselect one first.`);
      return;
    }
    state.selectedIds = [...state.selectedIds, id];
  }
  buildCast();
  buildRoom();
  resetRunForCastChange();
}

function syncExport() {
  const button = $("export");
  button.hidden = !state.run;
  button.disabled = !state.run;
  button.title = state.run ? `Download run ${state.run.run_id} as a zip` : "";
}

function resetRunForCastChange() {
  state.run = null;
  syncExport();
  state.votes = {};
  state.myVote = null;
  state.revealed = false;
  state.blind = false;
  state.blindOrder = null;
  $("blind").checked = false;
  $("reveal").hidden = true;
  $("castCard").hidden = false;
  $("usageCard").hidden = true;
  $("runMeta").textContent = "cast changed · run the room";
  applyLabels();
}

function buildRoom() {
  const room = $("room");
  room.replaceChildren();
  state.cardData = {};
  for (const persona of selectedPersonas()) {
    state.cardData[persona.id] = {
      name: persona.name,
      tagline: persona.tagline,
      approach: "",
      color: persona.color,
      ok: false,
      previewHref: "",
      direction: null,
    };
    room.append(personaCard(persona));
  }
  room.dataset.count = String(state.selectedIds.length);
  updateTagline();
  applyLabels();
}

function setStatus(card, text, kind = "") {
  const status = card.querySelector(".status");
  status.textContent = text;
  status.className = `status ${kind}`.trim();
}

function setThinking(card) {
  const personaId = card.dataset.persona;
  const skeleton = card.querySelector(".preview-skeleton");
  const iframe = card.querySelector("iframe");
  const error = card.querySelector(".error-box");
  if (error) error.remove();
  iframe.hidden = true;
  iframe.removeAttribute("src");
  iframe.removeAttribute("srcdoc");
  skeleton.hidden = false;
  skeleton.classList.remove("idle", "hidden");
  skeleton.textContent = "thinking…";
  if (state.cardData[personaId]) {
    state.cardData[personaId].approach = "The agent is working on its approach…";
    state.cardData[personaId].direction = null;
  }
  card.querySelector(".direction").textContent = "";
  setStatus(card, "thinking", "thinking");
  card.querySelector(".open-link").hidden = true;
  card.querySelector(".meta").textContent = "";
}

function renderResult(run, result) {
  const card = document.querySelector(`.card[data-persona="${result.persona.id}"]`);
  if (!card) return;
  const data = state.cardData[result.persona.id] || {};
  data.name = result.persona.name;
  data.tagline = result.persona.tagline;
  data.color = result.persona.color;
  data.approach = result.ok ? result.approach : "Generation failed.";
  data.ok = result.ok;
  data.previewHref = result.ok ? `/preview/${run.run_id}/${result.persona.id}` : "";
  data.direction = result.direction || null;
  state.cardData[result.persona.id] = data;

  const skeleton = card.querySelector(".preview-skeleton");
  const iframe = card.querySelector("iframe");
  const open = card.querySelector(".open-link");
  const meta = card.querySelector(".meta");
  const oldError = card.querySelector(".error-box");
  if (oldError) oldError.remove();

  meta.textContent = usageLine(result);

  if (result.ok) {
    const mode = modeOf(run);
    const is3D = mode !== "2d";
    iframe.removeAttribute("src");
    iframe.removeAttribute("srcdoc");
    if (is3D) {
      iframe.setAttribute("sandbox", "allow-scripts allow-same-origin");
      iframe.src = `http://${location.hostname}:8031/preview/${run.run_id}/${result.persona.id}`;
      data.previewHref = iframe.src;
    } else {
      iframe.setAttribute("sandbox", "allow-scripts");
      iframe.srcdoc = result.html;
      data.previewHref = `/preview/${run.run_id}/${result.persona.id}`;
    }
    iframe.hidden = false;
    skeleton.classList.add("hidden");
    open.href = data.previewHref;
    setStatus(card, "rendered", "ok");
  } else {
    iframe.hidden = true;
    skeleton.classList.add("hidden");
    const error = document.createElement("div");
    error.className = "error-box";
    error.textContent = result.error || "The agent returned no usable output.";
    card.querySelector(".preview-wrap").after(error);
    setStatus(card, "failed", "bad");
    open.hidden = true;
  }
}

function scalePreviews() {
  document.querySelectorAll(".preview-wrap").forEach((wrap) => {
    const iframe = wrap.querySelector("iframe");
    if (!iframe || iframe.hidden) return;
    const scale = wrap.clientWidth / 1080;
    iframe.style.transform = `scale(${scale})`;
  });
}

function renderUsage(run) {
  const card = $("usageCard");
  const body = $("usageBody");
  if (!run || !run.results || !run.results.length) {
    card.hidden = true;
    body.replaceChildren();
    return;
  }
  card.hidden = false;
  body.replaceChildren();

  const hidden = state.blind && !state.revealed;
  const order = hidden && state.blindOrder
    ? state.blindOrder
    : (run.cast || state.selectedIds);

  order.forEach((id, index) => {
    const result = run.results.find((row) => row.persona.id === id);
    if (!result) return;
    const u = result.usage || {};
    const letter = String.fromCharCode(65 + index);
    const row = document.createElement("tr");
    const cells = [
      [hidden ? `Agent ${letter}` : result.persona.name, "agent"],
      [Number(u.prompt_tokens || 0).toLocaleString(), "num"],
      [Number(u.completion_tokens || 0).toLocaleString(), "num"],
      [Number(u.total_tokens || 0).toLocaleString(), "num"],
      [fmtCost(u.cost_usd, u.cost_source), `num${u.cost_source === "estimated" || u.cost_source === "mixed" ? " est" : ""}`],
      [`${(result.elapsed_ms / 1000).toFixed(1)}s`, "num"],
      [Number(result.chars || 0).toLocaleString(), "num"],
      [result.ok ? "rendered" : "failed", result.ok ? "ok" : "bad"],
    ];
    for (const [text, className] of cells) {
      const td = document.createElement("td");
      td.textContent = text;
      if (className) td.className = className;
      row.append(td);
    }
    body.append(row);
  });

  const total = run.usage_total || run.results.reduce((acc, result) => {
    const u = result.usage || {};
    acc.prompt_tokens += Number(u.prompt_tokens || 0);
    acc.completion_tokens += Number(u.completion_tokens || 0);
    acc.total_tokens += Number(u.total_tokens || 0);
    return acc;
  }, { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0, cost_usd: null, cost_source: "unknown" });

  const totalRow = document.createElement("tr");
  totalRow.className = "total";
  const totalCells = [
    ["TOTAL", "agent"],
    [Number(total.prompt_tokens || 0).toLocaleString(), "num"],
    [Number(total.completion_tokens || 0).toLocaleString(), "num"],
    [Number(total.total_tokens || 0).toLocaleString(), "num"],
    [fmtCost(total.cost_usd, total.cost_source), "num"],
    [`${(run.elapsed_ms / 1000).toFixed(1)}s`, "num"],
    [Number(run.results.reduce((n, r) => n + (r.chars || 0), 0)).toLocaleString(), "num"],
    [`${run.results.filter((r) => r.ok).length}/${run.results.length} rendered`, ""],
  ];
  for (const [text, className] of totalCells) {
    const td = document.createElement("td");
    td.textContent = text;
    if (className) td.className = className;
    totalRow.append(td);
  }
  body.append(totalRow);

  $("usageTotals").textContent = `${fmtTokens(total.prompt_tokens)} in / ${fmtTokens(total.completion_tokens)} out · ${fmtCost(total.cost_usd, total.cost_source)} · ${(run.elapsed_ms / 1000).toFixed(1)}s`;
}

function applyLabels() {
  const room = $("room");
  if (!room) return;
  const baseOrder = state.selectedIds.length
    ? state.selectedIds
    : state.personas.map((p) => p.id);
  const order = state.blind && state.blindOrder ? state.blindOrder : baseOrder;
  for (const id of order) {
    const card = document.querySelector(`.card[data-persona="${id}"]`);
    if (card) room.append(card);
  }

  const maxVotes = Math.max(0, ...Object.values(state.votes));
  order.forEach((id, index) => {
    const card = document.querySelector(`.card[data-persona="${id}"]`);
    if (!card) return;
    const data = state.cardData[id] || {};
    const hidden = state.blind && !state.revealed;
    const letter = String.fromCharCode(65 + index);
    card.style.setProperty("--persona-color", hidden ? "#454b59" : (data.color || "#8b98a9"));
    card.querySelector(".card-name").textContent = hidden ? `Agent ${letter}` : (data.name || id);
    card.querySelector(".card-tagline").textContent = hidden
      ? "Identity hidden for blind voting."
      : (data.tagline || "");
    const approach = card.querySelector(".approach");
    approach.textContent = hidden
      ? "Approach hidden in blind mode. Judge only the motion."
      : (data.approach || "Waiting for the brief.");
    approach.classList.toggle("empty", !hidden && !data.approach);
    approach.title = hidden ? "" : (data.approach || "");

    const direction = card.querySelector(".direction");
    direction.textContent = hidden || !data.direction
      ? ""
      : `${data.direction.layout} · ${data.direction.camera} · ${data.direction.transition}`.replace(/_/g, " ");

    const open = card.querySelector(".open-link");
    open.hidden = hidden || !data.ok;
    open.href = data.previewHref || "#";

    const vote = card.querySelector(".vote-btn");
    vote.hidden = !hidden;
    vote.textContent = state.myVote === id ? "Voted" : "Vote";
    vote.classList.toggle("voted", state.myVote === id);
    vote.disabled = Boolean(state.myVote) && state.myVote !== id;

    const count = card.querySelector(".vote-count");
    const votes = state.votes[id] || 0;
    count.textContent = state.revealed && votes
      ? `${votes} vote${votes === 1 ? "" : "s"}`
      : "";

    card.classList.toggle(
      "winner",
      state.revealed && maxVotes > 0 && votes === maxVotes,
    );
  });
  renderUsage(state.run);
}

function castVote(id) {
  if (!state.blind || state.revealed) return;
  if (state.myVote === id) return;
  if (state.myVote && state.votes[state.myVote]) {
    state.votes[state.myVote] = Math.max(0, state.votes[state.myVote] - 1);
  }
  state.myVote = id;
  state.votes[id] = (state.votes[id] || 0) + 1;
  applyLabels();
}

function reveal() {
  state.revealed = true;
  state.blind = false;
  $("blind").checked = false;
  $("reveal").hidden = true;
  $("castCard").hidden = false;
  applyLabels();

  const entries = state.selectedIds.map((id) => {
    const persona = personaById(id);
    return { persona, votes: state.votes[id] || 0 };
  }).filter((entry) => entry.persona);
  const max = Math.max(0, ...entries.map((entry) => entry.votes));
  const usage = usageSummary(state.run);
  if (max === 0) {
    $("runMeta").textContent = `no votes cast${usage ? ` · ${usage}` : ""}`;
    return;
  }
  const winners = entries.filter((entry) => entry.votes === max).map((entry) => entry.persona.name);
  $("runMeta").textContent = `winner: ${winners.join(" + ")} · ${max} vote${max === 1 ? "" : "s"}${usage ? ` · ${usage}` : ""}`;
}

function setBlind(on) {
  state.blind = on;
  state.revealed = false;
  state.votes = {};
  state.myVote = null;
  state.blindOrder = on ? shuffle(state.selectedIds) : null;
  $("blind").checked = on;
  $("reveal").hidden = !on;
  $("castCard").hidden = on;
  if (on) {
    const usage = usageSummary(state.run);
    $("runMeta").textContent = `blind round · identities hidden${usage ? ` · ${usage}` : ""}`;
  }
  applyLabels();
}

let toastTimer = null;
function toast(text) {
  const el = $("toast");
  el.textContent = text;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 9000);
}

async function runRoom() {
  if (state.running) return;
  const brief = $("brief").value.trim();
  if (!brief) {
    toast("Write a brief first.");
    return;
  }
  if (state.selectedIds.length < 3) {
    toast("Choose at least 3 agents.");
    return;
  }
  state.running = true;
  state.run = null;
  state.votes = {};
  state.myVote = null;
  state.revealed = false;
  if (state.blind) state.blindOrder = shuffle(state.selectedIds);
  $("run").disabled = true;
  $("usageCard").hidden = true;
  $("runMeta").textContent = `${state.selectedIds.length} agents thinking…`;
  for (const card of document.querySelectorAll(".card")) setThinking(card);
  applyLabels();

  try {
    const res = await fetch("/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        brief,
        persona_ids: state.selectedIds,
        mode: state.mode,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    state.run = data;
    syncExport();
    for (const result of data.results) renderResult(data, result);
    applyLabels();
    requestAnimationFrame(scalePreviews);
    const ok = data.results.filter((r) => r.ok).length;
    const usage = usageSummary(data);
    $("runMeta").textContent = `${ok}/${data.results.length} generated · ${(data.elapsed_ms / 1000).toFixed(1)}s · ${modeLabel(modeOf(data))}${usage ? ` · ${usage}` : ""}`;
    if (ok === 0) toast("The room returned no usable outputs. Check the provider.");
  } catch (error) {
    $("runMeta").textContent = "run failed";
    toast(`Run failed: ${error.message}`);
    for (const card of document.querySelectorAll(".card")) setStatus(card, "failed", "bad");
  } finally {
    state.running = false;
    $("run").disabled = false;
  }
}

async function loadLatest() {
  try {
    const requested = new URLSearchParams(window.location.search).get("run");
    const res = await fetch(requested ? `/runs/${encodeURIComponent(requested)}` : "/latest");
    if (!res.ok) return;
    const run = await res.json();
    const cast = Array.isArray(run.cast) && run.cast.length
      ? run.cast
      : run.results.map((result) => result.persona.id);
    if (cast.length >= 3 && cast.length <= state.maxCast) {
      state.selectedIds = cast;
      buildCast();
      buildRoom();
    }
    state.run = run;
    syncExport();
    $("brief").value = run.brief;
    setMode(modeOf(run));
    for (const result of run.results) renderResult(run, result);
    applyLabels();
    requestAnimationFrame(scalePreviews);
    const ok = run.results.filter((r) => r.ok).length;
    const usage = usageSummary(run);
    $("runMeta").textContent = `latest · ${ok}/${run.results.length} · ${(run.elapsed_ms / 1000).toFixed(1)}s · ${modeLabel(modeOf(run))}${usage ? ` · ${usage}` : ""}`;
  } catch {
    /* no previous run */
  }
}

function resetCoreCast() {
  state.selectedIds = [...state.config.default_cast];
  buildCast();
  buildRoom();
  resetRunForCastChange();
}

async function init() {
  const res = await fetch("/config");
  state.config = await res.json();
  state.personas = state.config.personas || [];
  state.maxCast = state.config.max_cast || 8;
  state.selectedIds = [...(state.config.default_cast || state.personas.slice(0, 8).map((p) => p.id))];
  $("providerBadge").textContent = state.config.provider_label;
  $("brief").value = state.config.brief;
  buildCast();
  buildRoom();
  $("run").addEventListener("click", runRoom);
  $("export").addEventListener("click", () => {
    if (!state.run) return;
    const link = document.createElement("a");
    link.href = `/runs/${encodeURIComponent(state.run.run_id)}/export`;
    link.download = `troupe-${state.run.run_id}.zip`;
    document.body.append(link);
    link.click();
    link.remove();
  });
  $("coreCast").addEventListener("click", resetCoreCast);
  document.querySelectorAll(".mode-btn").forEach((button) => {
    button.addEventListener("click", () => setMode(button.dataset.mode));
  });
  setMode(state.config.mode_default || "2d");
  $("blind").addEventListener("change", (event) => {
    if (event.target.checked) setBlind(true);
    else reveal();
  });
  $("reveal").addEventListener("click", reveal);
  window.addEventListener("resize", scalePreviews);
  if ("ResizeObserver" in window) {
    const ro = new ResizeObserver(scalePreviews);
    document.querySelectorAll(".preview-wrap").forEach((el) => ro.observe(el));
  }
  await loadLatest();
}

init().catch((error) => {
  console.error(error);
  toast(`Startup error: ${error.message}`);
});
