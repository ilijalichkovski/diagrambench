/* GlyphBench viewer: polls /api/events, renders the display list into SVG,
   and tweens numeric attributes between successive scene states. */

const SVG_NS = "http://www.w3.org/2000/svg";
const canvas = document.getElementById("canvas");
const logEl = document.getElementById("log");

const NUMERIC = ["x", "y", "width", "height", "cx", "cy", "r", "x1", "y1",
  "x2", "y2", "opacity", "stroke-width", "font-size", "rx"];
const DUR = 460;

let nodes = new Map();   // id -> {el, attrs, text}
let since = 0;
let animQueue = [];
let animating = false;

// ---------------------------------------------------------------- utils
function lerp(a, b, t) { return a + (b - a) * t; }
function ease(t) { return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; }

function parseColor(c) {
  if (!c || c === "none") return null;
  if (c[0] === "#") {
    const h = c.length === 4
      ? c.slice(1).split("").map(x => x + x).join("") : c.slice(1);
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16),
      parseInt(h.slice(4, 6), 16)];
  }
  return null;
}
function fmtColor(rgb) {
  return "#" + rgb.map(v => Math.round(v).toString(16).padStart(2, "0")).join("");
}

function numbersOf(str) {
  return (String(str).match(/-?\d+\.?\d*/g) || []).map(Number);
}
function shapeOf(str) { return String(str).replace(/-?\d+\.?\d*/g, "#"); }
function fillNumbers(template, nums) {
  let i = 0;
  return template.replace(/#/g, () => {
    const v = nums[i++];
    return (Math.round(v * 100) / 100).toString();
  });
}

// ---------------------------------------------------------------- render
function setAttrs(el, attrs) {
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
}

function applyScene(items) {
  // returns an animation description executed over DUR ms
  const seen = new Set();
  const tweens = [];
  for (const it of items) {
    seen.add(it.id);
    let node = nodes.get(it.id);
    if (!node || node.el.tagName !== it.tag) {
      if (node) node.el.remove();
      const el = document.createElementNS(SVG_NS, it.tag);
      setAttrs(el, it.attrs);
      if (it.text !== undefined) el.textContent = it.text;
      el.setAttribute("opacity", 0);
      canvas.appendChild(el);
      node = { el, attrs: { ...it.attrs }, text: it.text };
      nodes.set(it.id, node);
      tweens.push({ kind: "fadein", el,
        to: it.attrs.opacity !== undefined ? it.attrs.opacity : 1 });
      continue;
    }
    // text swap
    if (it.text !== undefined && it.text !== node.text) {
      node.el.textContent = it.text;
      node.text = it.text;
    }
    for (const [k, v] of Object.entries(it.attrs)) {
      const old = node.attrs[k];
      if (old === v) continue;
      if (NUMERIC.includes(k) && isFinite(old) && isFinite(v)) {
        tweens.push({ kind: "num", el: node.el, attr: k,
          from: +old, to: +v });
      } else if ((k === "fill" || k === "stroke") &&
                 parseColor(old) && parseColor(v)) {
        tweens.push({ kind: "color", el: node.el, attr: k,
          from: parseColor(old), to: parseColor(v) });
      } else if ((k === "d" || k === "points") &&
                 shapeOf(old) === shapeOf(v)) {
        tweens.push({ kind: "path", el: node.el, attr: k,
          template: shapeOf(v), from: numbersOf(old), to: numbersOf(v) });
      } else {
        node.el.setAttribute(k, v);
      }
      node.attrs[k] = v;
    }
  }
  for (const [id, node] of [...nodes]) {
    if (!seen.has(id)) {
      tweens.push({ kind: "fadeout", el: node.el });
      nodes.delete(id);
    }
  }
  return tweens;
}

function runTweens(tweens, done) {
  if (!tweens.length) { done(); return; }
  const t0 = performance.now();
  function frame(now) {
    const t = Math.min((now - t0) / DUR, 1);
    const e = ease(t);
    for (const tw of tweens) {
      if (tw.kind === "num") {
        tw.el.setAttribute(tw.attr, lerp(tw.from, tw.to, e));
      } else if (tw.kind === "color") {
        tw.el.setAttribute(tw.attr,
          fmtColor([0, 1, 2].map(i => lerp(tw.from[i], tw.to[i], e))));
      } else if (tw.kind === "path") {
        const n = tw.to.map((v, i) =>
          lerp(tw.from[i] !== undefined ? tw.from[i] : v, v, e));
        tw.el.setAttribute(tw.attr, fillNumbers(tw.template, n));
      } else if (tw.kind === "fadein") {
        tw.el.setAttribute("opacity", lerp(0, tw.to, e));
      } else if (tw.kind === "fadeout") {
        tw.el.setAttribute("opacity", lerp(1, 0, e));
      }
    }
    if (t < 1) requestAnimationFrame(frame);
    else {
      for (const tw of tweens) if (tw.kind === "fadeout") tw.el.remove();
      done();
    }
  }
  requestAnimationFrame(frame);
}

// ---------------------------------------------------------------- log/UI
function addLog(html, cls) {
  const div = document.createElement("div");
  div.className = cls;
  div.textContent = html;
  logEl.appendChild(div);
  while (logEl.children.length > 400) logEl.removeChild(logEl.firstChild);
  document.getElementById("right").scrollTop = 1e9;
}

function setBadge(cls, text) {
  const b = document.getElementById("st-badge");
  b.className = "badge " + cls;
  b.textContent = text;
}

function updateStats(ev) {
  const c = ev.counts || {};
  const s = ev.stats || {};
  const t = ev.task;
  if (t) {
    document.getElementById("st-task").textContent =
      `${t.index}/${(s.tasks_total || 200)}`;
    document.getElementById("st-stage").textContent = t.stage;
    document.getElementById("task-id").textContent = t.id;
    document.getElementById("instruction").textContent = t.instruction;
  }
  document.getElementById("st-actions").textContent = c.total ?? 0;
  document.getElementById("st-ref").textContent = ev.ref_cost ?? "–";
  const regret = (c.total ?? 0) - (c.presents ?? 0) - (ev.ref_cost ?? 0);
  document.getElementById("st-regret").textContent =
    ev.ref_cost != null ? (regret >= 0 ? "+" + regret : regret) : "–";
  document.getElementById("st-life").textContent =
    `${s.tasks_done ?? 0}/${s.tasks_total ?? 0}`;
  document.getElementById("st-rate").textContent =
    s.success_rate != null ? Math.round(s.success_rate * 100) + "%" : "–";
  document.getElementById("st-mregret").textContent =
    s.recent_regret != null ? s.recent_regret : "–";
}

function showVerdict(v) {
  const el = document.getElementById("verdict");
  if (!v) { el.innerHTML = ""; return; }
  let html = `<div class="score">semantic ${(v.semantic_score * 100).toFixed(0)}% · ` +
    `layout ${(v.layout_score * 100).toFixed(0)}%</div>`;
  if (v.failed && v.failed.length) {
    html += "<ul>" + v.failed.slice(0, 6).map(f => `<li>${f}</li>`).join("") +
      "</ul>";
  }
  el.innerHTML = html;
}

// ---------------------------------------------------------------- events
function handle(ev, animate) {
  updateStats(ev);
  if (ev.kind === "task_start") {
    addLog(`▶ task ${ev.task ? ev.task.id : ""}`, "event start");
    showVerdict(null);
    setBadge("running", "constructing");
  }
  if (ev.log) {
    addLog("> " + ev.log.call, "call" + (ev.log.ok ? "" : " err"));
    if (ev.log.text) addLog(ev.log.text, "obs");
  }
  if (ev.kind === "present" && ev.verdict) {
    showVerdict(ev.verdict);
    if (ev.verdict.success) {
      addLog("✓ SUCCESS", "event success");
      setBadge("success", "success");
    } else {
      addLog("✗ not yet — " + (ev.verdict.failed[0] || ""), "event fail");
      setBadge("fail", "rejected");
    }
  }
  if (ev.finished) setBadge("success", "lifetime complete");
  if (ev.items) {
    animQueue.push(ev.items);
    if (animate) pump();
  }
}

function pump() {
  if (animating) return;
  // collapse backlog: skip straight to the newest pending scene
  while (animQueue.length > 2) animQueue.shift();
  const items = animQueue.shift();
  if (!items) return;
  animating = true;
  const tweens = applyScene(items);
  runTweens(tweens, () => { animating = false; pump(); });
}

function fastForward(items) {
  // apply a scene instantly (used when catching up on page load)
  const tweens = applyScene(items);
  for (const tw of tweens) {
    if (tw.kind === "num") tw.el.setAttribute(tw.attr, tw.to);
    else if (tw.kind === "color") tw.el.setAttribute(tw.attr, fmtColor(tw.to));
    else if (tw.kind === "path")
      tw.el.setAttribute(tw.attr, fillNumbers(tw.template, tw.to));
    else if (tw.kind === "fadein") tw.el.setAttribute("opacity", tw.to);
    else if (tw.kind === "fadeout") tw.el.remove();
  }
}

let caughtUp = false;

async function poll() {
  try {
    const r = await fetch(`/api/events?since=${since}`);
    const data = await r.json();
    const evs = data.events;
    if (!caughtUp && evs.length) {
      // first batch: render logs/stats, jump the canvas to the latest scene
      let lastItems = null;
      for (const ev of evs) {
        since = ev.seq + 1;
        const items = ev.items;
        delete ev.items;
        handle(ev, false);
        if (items) lastItems = items;
      }
      if (lastItems) fastForward(lastItems);
      caughtUp = true;
    } else {
      for (const ev of evs) {
        since = ev.seq + 1;
        handle(ev, true);
      }
    }
  } catch (e) { /* server briefly away; retry */ }
  setTimeout(poll, 280);
}

poll();
