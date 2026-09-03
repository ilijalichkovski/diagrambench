/* DiagramBench sandbox live viewer: live file tree + per-entry project
   reconstruction, full model trajectory (codex), toolchain timeline, and the
   artifact (SVG/ASCII) — all scrubbable. */

const $ = (id) => document.getElementById(id);

let seq = -1;
let trajSince = 0;
let follow = true;
let mode = "svg";
let rightTab = "traj";
let selectedEntry = null;   // entry index being viewed (null = live head)
let selectedFile = null;
let entryFiles = null;      // {path: content} when scrubbed to an entry
let lastState = null;

// ------------------------------------------------------------- header/left
function setConn(state) {
  const b = $("st-conn");
  if (state.finished) { b.className = "badge ok"; b.textContent = "run complete"; }
  else if (state.terminated) { b.className = "badge err"; b.textContent = "run over"; }
  else if (state.connected) { b.className = "badge ok"; b.textContent = "live"; }
  else { b.className = "badge err";
         b.textContent = "unreachable — showing last state"; }
}

function renderStats(s) {
  $("st-source").textContent = s.source || "–";
  if (s.level) {
    $("st-level").textContent = `${s.level.index}/${s.num_levels}`;
    $("instruction").textContent = s.level.instruction;
  } else if (s.finished) {
    $("st-level").textContent = "done";
    $("instruction").textContent = "All levels complete.";
  }
  $("st-cleared").textContent = s.cleared;
  if (s.budget) {
    $("st-tc").textContent = `${s.budget.tc}/40`;
    $("st-presents").textContent = `${s.budget.presents}/3`;
  }
}

function renderFiles(s) {
  const tree = $("filetree");
  tree.innerHTML = "";
  const scrubbed = entryFiles !== null;
  $("files-scope").textContent = scrubbed
    ? `@ entry #${selectedEntry}` : "· live";
  const dirty = new Set(scrubbed ? [] : (s?.dirty || []));
  $("dirty-note").textContent = dirty.size ? ` · ${dirty.size} unbuilt` : "";
  const paths = scrubbed ? Object.keys(entryFiles)
    : (s?.live_files || []);
  for (const p of paths) {
    const li = document.createElement("li");
    const short = scrubbed ? p : (p.split("/").slice(2).join("/") || p);
    li.textContent = short;
    if (dirty.has(p)) {
      const d = document.createElement("span");
      d.className = "dirty";
      d.textContent = "● unbuilt";
      li.appendChild(d);
    }
    if (p === selectedFile) li.classList.add("on");
    li.onclick = () => { selectedFile = p; showFile(p); renderFiles(s); };
    tree.appendChild(li);
  }
  if (paths.length && (!selectedFile || !paths.includes(selectedFile))) {
    selectedFile = paths.find((p) => p.endsWith(".sgl")) || paths[0];
    showFile(selectedFile);
  }
  if (!paths.length) { $("filebody").textContent = ""; }
}

async function showFile(p) {
  if (entryFiles !== null) {
    $("filebody").textContent = entryFiles[p] ?? "";
    return;
  }
  try {
    const r = await fetch(`/api/file?p=${encodeURIComponent(p)}`);
    const d = await r.json();
    $("filebody").textContent = d.content ?? d.error ?? "";
  } catch (e) { /* transient */ }
}

// ------------------------------------------------------------- toolchain
function classify(e) {
  let cls = e.k;
  const t = e.text || "";
  if (t.includes("fault ") || t.includes("build: failed") ||
      t.includes("trapped") || t.startsWith("NOT YET") ||
      t.includes("RUN OVER")) cls += " fail";
  if (e.cleared) cls += " cleared";
  return cls;
}

function renderTimeline(s) {
  const tl = $("timeline");
  tl.innerHTML = "";
  let lastLevel = null;
  for (const e of s.entries) {
    if (e.level_index !== lastLevel) {
      lastLevel = e.level_index;
      const m = document.createElement("div");
      m.className = "milestone";
      m.textContent = `— level ${e.level_index} · ${e.level_id} —`;
      tl.appendChild(m);
    }
    const div = document.createElement("div");
    div.className = "ev " + classify(e);
    const label = e.k + (e.k === "build" && e.n_files
      ? ` (${e.n_files} files)` : "") + (e.code ? ` ${e.code}` : "");
    div.innerHTML = `<div class="head"><span class="kind"></span>` +
      `<span class="lvl">tc ${e.tc}/40 · p ${e.presents}/3</span></div>` +
      `<div class="txt"></div>`;
    div.querySelector(".kind").textContent = label;
    div.querySelector(".txt").textContent =
      (e.text || "").split("\n").slice(0, 4).join("\n");
    if (e.i === selectedEntry) div.classList.add("on");
    div.onclick = () => { follow = false; syncFollowBtn(); selectEntry(e.i); };
    tl.appendChild(div);
  }
  if (follow && rightTab === "tool") $("right").scrollTop = 1e9;
}

// ------------------------------------------------------------- trajectory
function trajBlock(ev) {
  const div = document.createElement("div");
  div.className = "tj " + ev.kind;
  const who = document.createElement("div");
  who.className = "who";
  const body = document.createElement("div");
  body.className = "body";
  body.textContent = ev.text || "";
  if (ev.kind === "reasoning") who.textContent = "thinking";
  else if (ev.kind === "assistant") who.textContent = "assistant";
  else if (ev.kind === "user") {
    who.textContent = "user / environment";
    div.onclick = () => div.classList.toggle("open");
  } else if (ev.kind === "tool_call") {
    who.textContent = ev.name || "tool";
    if (ev.entries && ev.entries.length) {
      div.classList.add("sigil");
      const link = document.createElement("span");
      link.className = "link";
      link.textContent = `→ view result #${ev.entries[ev.entries.length - 1]}`;
      who.appendChild(link);
      div.onclick = () => {
        follow = false;
        syncFollowBtn();
        selectEntry(ev.entries[ev.entries.length - 1]);
      };
    }
  } else if (ev.kind === "tool_out") {
    who.textContent = "output";
    div.onclick = () => div.classList.toggle("open");
  }
  div.appendChild(who);
  div.appendChild(body);
  return div;
}

async function pollTraj() {
  try {
    const r = await fetch(`/api/traj?since=${trajSince}`);
    const d = await r.json();
    if (d.events && d.events.length) {
      const tv = $("trajview");
      for (const ev of d.events) tv.appendChild(trajBlock(ev));
      trajSince = d.total;
      while (tv.children.length > 900) tv.removeChild(tv.firstChild);
      if (follow && rightTab === "traj") $("right").scrollTop = 1e9;
    }
  } catch (e) { /* transient */ }
}

// ------------------------------------------------------------- scene/scrub
async function selectEntry(i) {
  selectedEntry = i;
  try {
    const r = await fetch(`/api/entry/${i}`);
    const d = await r.json();
    if (d.error) return;
    showScene(d.snapshot, d.snapshot_i, i);
    entryFiles = d.files || {};
    selectedFile = Object.keys(entryFiles)
      .find((p) => p.startsWith("src/")) || Object.keys(entryFiles)[0];
    renderFiles(lastState);
    if (selectedFile) showFile(selectedFile);
  } catch (e) { /* transient */ }
  if (lastState) renderTimeline(lastState);
}

function showScene(snap, snapI, atI) {
  const label = $("scene-label");
  if (!snap || (!snap.svg && !snap.ascii)) {
    $("scene-svg").innerHTML =
      `<div class="empty">no successful run yet on this level</div>`;
    $("scene-ascii").textContent = "";
    label.textContent = "artifact — nothing rendered yet";
    return;
  }
  label.textContent = atI == null || snapI == null || snapI === atI
    ? "artifact — after latest run"
    : `artifact — as of run #${snapI} (viewing entry #${atI})`;
  $("scene-svg").innerHTML = snap.svg || "";
  $("scene-ascii").textContent = snap.ascii || "";
}

function latestSceneEntry(s) {
  for (let j = s.entries.length - 1; j >= 0; j--) {
    if (s.entries[j].has_scene) return s.entries[j].i;
  }
  return s.entries.length ? s.entries[s.entries.length - 1].i : null;
}

function goLive(s) {
  entryFiles = null;
  selectedEntry = null;
  selectedFile = null;
  renderFiles(s);
  const i = latestSceneEntry(s);
  if (i != null) {
    fetch(`/api/entry/${i}`).then((r) => r.json()).then((d) => {
      if (!d.error) showScene(d.snapshot, d.snapshot_i, null);
    }).catch(() => {});
  }
}

// ------------------------------------------------------------- controls
function syncFollowBtn() { $("follow").classList.toggle("on", follow); }

function syncMode() {
  $("mode-svg").classList.toggle("on", mode === "svg");
  $("mode-ascii").classList.toggle("on", mode === "ascii");
  $("scene-svg").classList.toggle("hidden", mode !== "svg");
  $("scene-ascii").classList.toggle("hidden", mode !== "ascii");
}

function syncTabs() {
  $("tab-traj").classList.toggle("on", rightTab === "traj");
  $("tab-tool").classList.toggle("on", rightTab === "tool");
  $("trajview").classList.toggle("hidden", rightTab !== "traj");
  $("timeline").classList.toggle("hidden", rightTab !== "tool");
}

$("mode-svg").onclick = () => { mode = "svg"; syncMode(); };
$("mode-ascii").onclick = () => { mode = "ascii"; syncMode(); };
$("tab-traj").onclick = () => { rightTab = "traj"; syncTabs(); };
$("tab-tool").onclick = () => { rightTab = "tool"; syncTabs(); };
$("follow").onclick = () => {
  follow = !follow;
  syncFollowBtn();
  if (follow && lastState) goLive(lastState);
};

// ------------------------------------------------------------- main loop
async function poll() {
  try {
    const r = await fetch("/api/state");
    const s = await r.json();
    lastState = s;
    setConn(s);
    if (s.seq !== seq) {
      seq = s.seq;
      renderStats(s);
      renderTimeline(s);
      if (follow) {
        goLive(s);
      } else {
        renderFiles(s);
      }
    }
    await pollTraj();
  } catch (e) { /* server briefly away */ }
  setTimeout(poll, 1500);
}

syncMode();
syncFollowBtn();
syncTabs();
poll();
