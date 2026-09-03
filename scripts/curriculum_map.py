"""Generate the curriculum mega-map: a single self-contained HTML file showing
where every SIGIL primitive/concept is introduced and where it is retested
across the 200-level lifetime — zoomable, clickable, with lineage arcs.

Run:  .venv/bin/python scripts/curriculum_map.py   → docs/curriculum-map.html
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from diagrambench.sdk import OPS  # noqa: E402
from diagrambench.tasks import load_curriculum  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "docs",
                   "curriculum-map.html")

PREFIX_FAMILY = {"form": "sowing", "trait": "metering", "law": "settling",
                 "relation": "data", "mode": "data", "derive": "data",
                 "carve": "ground", "rim": "guides", "badge": "script",
                 "hoop": "ground", "nest": "ground"}
FAMILY_OF_OP = {name: od.family for name, od in OPS.items()}
FAMILY_RENAME = {"ledgers": "data", "helm": "control", "oracle": "control"}


def concept_meta(c):
    if ":" in c:
        prefix, val = c.split(":", 1)
        return val, prefix, PREFIX_FAMILY.get(prefix, "misc")
    fam = FAMILY_OF_OP.get(c, "misc")
    return c, "op", FAMILY_RENAME.get(fam, fam)


def build_data():
    tasks = load_curriculum()
    concepts = {}
    for t in tasks:
        for c in t["required_concepts"]:
            rec = concepts.setdefault(c, {"uses": []})
            rec["uses"].append(t["index"])
    order = sorted(concepts, key=lambda c: (concepts[c]["uses"][0], c))
    cidx = {c: i for i, c in enumerate(order)}

    concept_rows = []
    for c in order:
        name, tag, fam = concept_meta(c)
        uses = concepts[c]["uses"]
        gaps = [uses[k] for k in range(1, len(uses))
                if uses[k] - uses[k - 1] >= 50]
        concept_rows.append({"n": name, "t": tag, "f": fam,
                             "i": uses[0], "u": uses, "g": gaps})

    levels = []
    for t in tasks:
        levels.append({
            "x": t["index"], "s": t["stage"], "id": t["id"],
            "d": t["difficulty"]["concepts"],
            "a": t["difficulty"]["ref_actions"],
            "q": t["instruction"],
            "new": [cidx[c] for c in t["new_concepts"]],
            "req": sorted(cidx[c] for c in t["required_concepts"]),
        })
    stages = [
        {"s": 1, "lo": 1, "hi": 25, "label": "1 · primitive discovery"},
        {"s": 2, "lo": 26, "hi": 60, "label": "2 · short compositions"},
        {"s": 3, "lo": 61, "hi": 110, "label": "3 · medium compositions"},
        {"s": 4, "lo": 111, "hi": 160, "label": "4 · advanced composition"},
        {"s": 5, "lo": 161, "hi": 200, "label": "5 · mastery + plasticity"},
    ]
    return {"concepts": concept_rows, "levels": levels, "stages": stages}


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DiagramBench Curriculum Map</title>
<style>
:root {
  --ground:#F2F2EE; --panel:#FFFFFF; --ink:#1F2430; --muted:#66707F;
  --faint:#9AA1AE; --line:#E4E6EB; --intro:#D14E08; --reuse:#3E6DE0;
  --grid:#ECEDF1; --stripe:#F7F7F4; --dim:0.14;
  --s1:#DCE4F8; --s2:#C2D1F4; --s3:#9DB6EE; --s4:#7093E7; --s5:#3E6DE0;
}
@media (prefers-color-scheme: dark) { :root {
  --ground:#14171E; --panel:#1C202A; --ink:#E7EAF1; --muted:#A2ABBA;
  --faint:#6E7686; --line:#2C3240; --intro:#E06A2B; --reuse:#5B82E8;
  --grid:#252B37; --stripe:#191D26;
  --s1:#262E40; --s2:#303C58; --s3:#3D4F77; --s4:#4C64A0; --s5:#6E93F0;
}}
:root[data-theme="light"] {
  --ground:#F2F2EE; --panel:#FFFFFF; --ink:#1F2430; --muted:#66707F;
  --faint:#9AA1AE; --line:#E4E6EB; --intro:#D14E08; --reuse:#3E6DE0;
  --grid:#ECEDF1; --stripe:#F7F7F4;
  --s1:#DCE4F8; --s2:#C2D1F4; --s3:#9DB6EE; --s4:#7093E7; --s5:#3E6DE0;
}
:root[data-theme="dark"] {
  --ground:#14171E; --panel:#1C202A; --ink:#E7EAF1; --muted:#A2ABBA;
  --faint:#6E7686; --line:#2C3240; --intro:#E06A2B; --reuse:#5B82E8;
  --grid:#252B37; --stripe:#191D26;
  --s1:#262E40; --s2:#303C58; --s3:#3D4F77; --s4:#4C64A0; --s5:#6E93F0;
}
* { box-sizing: border-box; }
html, body { height: 100%; }
body { margin:0; background:var(--ground); color:var(--ink); overflow:hidden;
  font-family: Inter,-apple-system,'Segoe UI','Helvetica Neue',Arial,sans-serif; }
#bar { display:flex; align-items:center; gap:18px; padding:10px 16px;
  background:var(--panel); border-bottom:1px solid var(--line); flex-wrap:wrap; }
#bar h1 { font-size:15px; margin:0; letter-spacing:-0.01em; }
#bar h1 span { color:var(--reuse); }
.chip { display:flex; align-items:center; gap:6px; font-size:11px;
  color:var(--muted); }
.sw { width:10px; height:10px; border-radius:2px; }
.sw.dot { border-radius:50%; width:7px; height:7px; }
.btn { font-size:11px; font-weight:600; padding:4px 12px; border-radius:14px;
  border:1px solid var(--line); background:var(--panel); color:var(--muted);
  cursor:pointer; }
.btn:hover { border-color: var(--reuse); color: var(--reuse); }
#hint { font-size:11px; color:var(--faint); margin-left:auto; }
#stage { position:relative; width:100%; height:calc(100% - 46px); }
svg { width:100%; height:100%; display:block; cursor:grab; }
svg.panning { cursor:grabbing; }
text { font-family:inherit; }
#tip { position:absolute; pointer-events:none; background:var(--panel);
  border:1px solid var(--line); border-radius:8px; padding:8px 10px;
  font-size:11px; line-height:1.45; max-width:340px; display:none;
  box-shadow:0 4px 18px rgba(10,14,25,0.14); z-index:5; }
#tip .h { font-weight:700; }
#tip .m { color:var(--muted); }
#inspector { position:absolute; top:12px; right:12px; width:320px;
  max-height:calc(100% - 24px); overflow-y:auto; background:var(--panel);
  border:1px solid var(--line); border-radius:12px; padding:14px 16px;
  font-size:12px; line-height:1.5; display:none; z-index:4;
  box-shadow:0 6px 24px rgba(10,14,25,0.14); }
#inspector h3 { margin:0 0 2px; font-size:13px; }
#inspector .sub { color:var(--muted); font-size:11px; margin-bottom:8px; }
#inspector .close { float:right; cursor:pointer; color:var(--faint);
  font-size:14px; border:none; background:none; }
#inspector ul { margin:6px 0 0; padding-left:0; list-style:none; }
#inspector li { padding:2px 0; cursor:pointer; display:flex; gap:6px;
  align-items:baseline; }
#inspector li:hover { color:var(--reuse); }
#inspector li .tag { font-size:9px; color:var(--faint); text-transform:
  uppercase; letter-spacing:0.05em; min-width:44px; }
#inspector li.new .name { color:var(--intro); font-weight:700; }
#inspector .stat { display:inline-block; margin-right:12px;
  color:var(--muted); }
#inspector .stat b { color:var(--ink); }
</style>
</head>
<body>
<div id="bar">
  <h1>DiagramBench <span>curriculum map</span></h1>
  <span class="chip"><span class="sw" style="background:var(--intro)"></span>introduced</span>
  <span class="chip"><span class="sw dot" style="background:var(--reuse)"></span>retested</span>
  <span class="chip"><span class="sw dot" style="background:var(--reuse);box-shadow:0 0 0 2px var(--intro)"></span>retested after ≥50-level gap</span>
  <span class="chip"><span class="sw" style="background:linear-gradient(90deg,var(--s1),var(--s5))"></span>stages 1–5</span>
  <button class="btn" id="fit">fit</button>
  <button class="btn" id="clear">clear selection</button>
  <span id="hint">wheel = zoom · drag = pan · click a level column or a concept label</span>
</div>
<div id="stage">
  <svg id="svg"><g id="world"></g><g id="overlay-fixed"></g></svg>
  <div id="tip"></div>
  <div id="inspector"></div>
</div>
<script>
const DATA = %%DATA%%;

// ---------------------------------------------------------------- geometry
const GUT = 236;            // left gutter for concept labels
const HDR = 118;            // header height (stages, depth bars, ticks)
const CW = 7.2, RH = 13.2;  // cell size
const NC = DATA.concepts.length, NL = DATA.levels.length;
const W = GUT + NL * CW + 30, H = HDR + NC * RH + 30;

const css = (n) => getComputedStyle(document.documentElement)
  .getPropertyValue(n).trim();
const svg = document.getElementById("svg");
const world = document.getElementById("world");
const NS = "http://www.w3.org/2000/svg";
function el(tag, attrs, parent, text) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  (parent || world).appendChild(e);
  if (text !== undefined) e.textContent = text;
  return e;
}
const X = (lvl) => GUT + (lvl - 1) * CW;   // level index (1-based) -> x
const Y = (row) => HDR + row * RH;

// ---------------------------------------------------------------- build
const rowsG = el("g", {}), arcsG = el("g", {}), hitsG = el("g", {});
const maxDepth = Math.max(...DATA.levels.map((l) => l.d));

function build() {
  // stage bands + labels
  for (const st of DATA.stages) {
    el("rect", {x: X(st.lo), y: 0, width: (st.hi - st.lo + 1) * CW,
      height: 16, rx: 3, fill: css("--s" + st.s)});
    el("text", {x: X(st.lo) + 5, y: 11.5, "font-size": 9.5,
      "font-weight": 600, fill: st.s >= 4 ? "#FFFFFF" : css("--ink"),
      "letter-spacing": "0.04em"}, world, st.label);
  }
  // composition-depth bars + intro ticks
  el("text", {x: GUT - 8, y: 52, "font-size": 9, fill: css("--faint"),
    "text-anchor": "end"}, world, "concepts per level →");
  el("text", {x: GUT - 8, y: 94, "font-size": 9, fill: css("--faint"),
    "text-anchor": "end"}, world, "introductions →");
  for (const l of DATA.levels) {
    const h = 34 * l.d / maxDepth;
    el("rect", {x: X(l.x) + 1, y: 56 - h, width: CW - 2, height: h,
      fill: css("--reuse"), opacity: 0.75, rx: 1});
    if (l.new.length) {
      const hh = 4 + 3.4 * l.new.length;
      el("rect", {x: X(l.x) + 1, y: 96 - hh, width: CW - 2, height: hh,
        fill: css("--intro"), rx: 1});
    }
    if (l.x % 10 === 0 || l.x === 1) {
      el("text", {x: X(l.x) + CW / 2, y: 108, "font-size": 8,
        fill: css("--faint"), "text-anchor": "middle"}, world, l.x);
    }
  }
  // rows
  DATA.concepts.forEach((c, r) => {
    const g = el("g", {class: "row", "data-r": r}, rowsG);
    if (r % 2 === 0) {
      el("rect", {x: 0, y: Y(r), width: W, height: RH,
        fill: css("--stripe")}, g);
    }
    el("text", {x: GUT - 54, y: Y(r) + RH - 3.6, "font-size": 9.5,
      "text-anchor": "end", fill: css("--ink"), class: "lbl",
      "data-r": r, style: "cursor:pointer"}, g, c.n);
    el("text", {x: GUT - 50, y: Y(r) + RH - 3.6, "font-size": 7.5,
      fill: css("--faint")}, g, c.t === "op" ? c.f : c.t);
    const gapSet = new Set(c.g);
    for (const lvl of c.u) {
      const cx = X(lvl) + CW / 2, cy = Y(r) + RH / 2;
      if (lvl === c.i) {
        el("rect", {x: cx - 3.4, y: cy - 3.4, width: 6.8, height: 6.8,
          rx: 1.6, fill: css("--intro")}, g);
      } else {
        if (gapSet.has(lvl)) {
          el("circle", {cx, cy, r: 4.1, fill: "none",
            stroke: css("--intro"), "stroke-width": 1.4}, g);
        }
        el("circle", {cx, cy, r: 2.1, fill: css("--reuse"),
          opacity: 0.8}, g);
      }
    }
  });
  // faint column separators each 25 levels
  for (let x = 25; x < NL; x += 25) {
    el("line", {x1: X(x + 1) - CW / 2 + CW / 2, y1: HDR - 4,
      x2: X(x + 1), y2: H - 20, stroke: css("--grid"),
      "stroke-width": 1}, world);
  }
  // hit columns
  DATA.levels.forEach((l) => {
    el("rect", {x: X(l.x), y: 0, width: CW, height: H - 20,
      fill: "transparent", class: "hit", "data-x": l.x}, hitsG);
  });
  world.appendChild(rowsG);
  world.appendChild(arcsG);
  world.appendChild(hitsG);
}
build();

// ---------------------------------------------------------------- pan/zoom
let tx = 0, ty = 0, k = 1;
function apply() {
  world.setAttribute("transform",
    `translate(${tx},${ty}) scale(${k})`);
}
function fit() {
  const vw = svg.clientWidth, vh = svg.clientHeight;
  k = Math.min(vw / W, vh / H);
  tx = (vw - W * k) / 2; ty = (vh - H * k) / 2;
  apply();
}
svg.addEventListener("wheel", (e) => {
  e.preventDefault();
  const f = Math.exp(-e.deltaY * 0.0016);
  const nk = Math.min(Math.max(k * f, 0.15), 12);
  const r = svg.getBoundingClientRect();
  const mx = e.clientX - r.left, my = e.clientY - r.top;
  tx = mx - (mx - tx) * (nk / k);
  ty = my - (my - ty) * (nk / k);
  k = nk; apply();
}, {passive: false});
let pan = null;
svg.addEventListener("mousedown", (e) => {
  pan = {x: e.clientX, y: e.clientY, tx, ty};
  svg.classList.add("panning");
});
window.addEventListener("mousemove", (e) => {
  if (!pan) return;
  tx = pan.tx + e.clientX - pan.x; ty = pan.ty + e.clientY - pan.y; apply();
});
window.addEventListener("mouseup", () => {
  pan = null; svg.classList.remove("panning");
});
document.getElementById("fit").onclick = fit;
window.addEventListener("resize", fit);

// ---------------------------------------------------------------- tooltip
const tip = document.getElementById("tip");
function showTip(html, e) {
  tip.innerHTML = html;
  tip.style.display = "block";
  const r = document.getElementById("stage").getBoundingClientRect();
  let x = e.clientX - r.left + 14, y = e.clientY - r.top + 14;
  if (x + 350 > r.width) x = e.clientX - r.left - 354;
  if (y + tip.offsetHeight + 20 > r.height)
    y = e.clientY - r.top - tip.offsetHeight - 10;
  tip.style.left = x + "px"; tip.style.top = y + "px";
}
function hideTip() { tip.style.display = "none"; }

// ---------------------------------------------------------------- select
const insp = document.getElementById("inspector");
let sel = null;
function dimRows(keep) {
  document.querySelectorAll("#world .row").forEach((g) => {
    g.style.opacity = keep && !keep.has(+g.dataset.r)
      ? css("--dim") : 1;
  });
}
function clearSel() {
  sel = null;
  arcsG.innerHTML = "";
  dimRows(null);
  insp.style.display = "none";
}
document.getElementById("clear").onclick = clearSel;
window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") clearSel();
});

function arc(x1, y1, x2, y2, color, op) {
  const d = Math.abs(x2 - x1);
  const lift = Math.min(90, 14 + d * 0.12);
  el("path", {d: `M${x1},${y1} C${x1},${y1 - lift} ${x2},${y2 - lift} ` +
    `${x2},${y2}`, fill: "none", stroke: color, "stroke-width": 1.2,
    opacity: op}, arcsG);
}

function selectLevel(x) {
  clearSel();
  const l = DATA.levels[x - 1];
  sel = {type: "level", x};
  const keep = new Set(l.req);
  dimRows(keep);
  el("rect", {x: X(x), y: 16, width: CW, height: H - 36, fill: "none",
    stroke: css("--intro"), "stroke-width": 1.4, rx: 2}, arcsG);
  for (const r of l.req) {
    const c = DATA.concepts[r];
    if (c.i !== x) {
      arc(X(c.i) + CW / 2, Y(r) + RH / 2, X(x) + CW / 2, Y(r) + RH / 2,
          css("--reuse"), 0.5);
    }
  }
  const newSet = new Set(l.new);
  insp.innerHTML = `<button class="close">×</button>
    <h3>Level ${l.x} · ${l.id}</h3>
    <div class="sub">stage ${l.s} · ${l.d} concepts ·
      ${l.a} reference statements</div>
    <div>${l.q}</div>
    <div style="margin-top:8px"><span class="stat"><b>${l.new.length}</b>
      introduced here</span><span class="stat"><b>${l.req.length -
      l.new.length}</b> retested</span></div>
    <ul>` + l.req.map((r) => {
      const c = DATA.concepts[r];
      return `<li class="${newSet.has(r) ? "new" : ""}" data-r="${r}">
        <span class="tag">${c.t === "op" ? c.f : c.t}</span>
        <span class="name">${c.n}</span>
        <span class="tag" style="margin-left:auto">intro L${c.i}</span></li>`;
    }).join("") + `</ul>`;
  insp.style.display = "block";
}

function selectConcept(r) {
  clearSel();
  const c = DATA.concepts[r];
  sel = {type: "concept", r};
  dimRows(new Set([r]));
  for (const lvl of c.g) {
    const prev = c.u[c.u.indexOf(lvl) - 1];
    arc(X(prev) + CW / 2, Y(r) + RH / 2, X(lvl) + CW / 2, Y(r) + RH / 2,
        css("--intro"), 0.7);
  }
  const gaps = c.u.slice(1).map((v, i) => v - c.u[i]);
  const maxGap = gaps.length ? Math.max(...gaps) : 0;
  insp.innerHTML = `<button class="close">×</button>
    <h3>${c.n}</h3>
    <div class="sub">${c.t === "op" ? "operation" : c.t} ·
      family ${c.f}</div>
    <div><span class="stat">introduced <b>L${c.i}</b></span>
      <span class="stat"><b>${c.u.length}</b> levels use it</span>
      <span class="stat">longest gap <b>${maxGap}</b></span></div>
    ${c.i > 110 ? '<div style="color:var(--intro);font-weight:600;' +
      'margin-top:4px">plasticity probe — introduced late in life</div>' : ""}
    <ul>` + c.u.map((lvl) => {
      const l = DATA.levels[lvl - 1];
      return `<li data-x="${lvl}"><span class="tag">L${lvl} · s${l.s}</span>
        <span class="name">${lvl === c.i ? "★ introduced — " : ""}
        ${l.q.slice(0, 64)}…</span></li>`;
    }).join("") + `</ul>`;
  insp.style.display = "block";
}

insp.addEventListener("click", (e) => {
  if (e.target.classList.contains("close")) { clearSel(); return; }
  const li = e.target.closest("li");
  if (!li) return;
  if (li.dataset.r !== undefined) selectConcept(+li.dataset.r);
  else if (li.dataset.x !== undefined) selectLevel(+li.dataset.x);
});

// ---------------------------------------------------------------- hover
let downAt = null;
svg.addEventListener("mousedown", (e) => { downAt = [e.clientX, e.clientY]; });
svg.addEventListener("mousemove", (e) => {
  const t = e.target;
  if (t.classList && t.classList.contains("hit")) {
    const l = DATA.levels[+t.dataset.x - 1];
    showTip(`<div class="h">Level ${l.x} · ${l.id} · stage ${l.s}</div>
      <div class="m">${l.q.slice(0, 180)}${l.q.length > 180 ? "…" : ""}</div>
      <div class="m">${l.d} concepts · ${l.new.length} new · click to
      inspect</div>`, e);
  } else if (t.classList && t.classList.contains("lbl")) {
    const c = DATA.concepts[+t.dataset.r];
    showTip(`<div class="h">${c.n} <span class="m">(${c.t === "op"
      ? c.f : c.t})</span></div>
      <div class="m">introduced L${c.i} · used by ${c.u.length} levels ·
      click to inspect</div>`, e);
  } else hideTip();
});
svg.addEventListener("click", (e) => {
  if (downAt && Math.hypot(e.clientX - downAt[0],
      e.clientY - downAt[1]) > 4) return;   // it was a pan
  const t = e.target;
  if (t.classList && t.classList.contains("hit")) selectLevel(+t.dataset.x);
  else if (t.classList && t.classList.contains("lbl"))
    selectConcept(+t.dataset.r);
  else clearSel();
});

fit();
</script>
</body>
</html>
"""


def main():
    data = build_data()
    html = TEMPLATE.replace("%%DATA%%", json.dumps(data))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(html)
    n = len(data["concepts"])
    marks = sum(len(c["u"]) for c in data["concepts"])
    print(f"wrote {OUT}: {n} concepts × {len(data['levels'])} levels, "
          f"{marks} marks, {len(html) // 1024} KB")


if __name__ == "__main__":
    main()
