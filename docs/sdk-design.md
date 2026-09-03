# SIGIL — the DiagramBench instrument (developer documentation)

> **This document is for benchmark developers only. The agent must never see
> it.** The agent gets a project folder, the `./sigil` toolchain, a terse
> grammar card (`sigil grammar`, which costs budget), and compiler faults —
> everything else must be inferred through building, running, and studying its
> own renders.

SIGIL (**S**taged **I**nstruction **G**rammar for **I**llustrated **L**ayouts)
is the single, persistent instrument at the heart of DiagramBench. It has two
layers:

1. **The language & toolchain** (agent-facing): a compiled, multi-file,
   aspect-locked DSL. The agent writes `.sgl` units, compiles them
   (`sigil build`), executes them (`sigil run` — which always renders the
   artifact back), and submits (`sigil present`).
2. **The scene engine** (internal): a semantic scene the programs lower onto —
   the representation the verifier reads. Never pixels.

The instrument never resets or changes across the 200-level lifetime.

---

## 1. The working loop

Each level is a sandboxed project folder; levels unlock strictly in order.

```
levels/L026/
├── BRIEF.md            the instruction (the only task statement)
├── sigil.toml          manifest: unit list, view mode, ASCII grid size
├── data/*.tsv          inputs — schemas must be declared to load them
├── src/*.sgl           the agent's units
└── out/                render.txt (ASCII), render.svg, render.png (image mode)

./sigil status            free — level, budgets, files
./sigil grammar           the grammar card               (costs 1)
./sigil build             compile src/*.sgl → IR         (costs 1)
./sigil run               execute IR; ALWAYS renders     (costs 1)
./sigil explain F244      one fault code, tersely        (costs 1)
./sigil present           submit for hidden verification (3 per level)
```

**Budgets: 40 toolchain invocations and 3 presents per level; exhausting
either ends the entire run.** With presents that scarce, the render is the
agent's only cheap feedback — studying your own output is the game.

---

## 2. The language

### Aspect-locked translation units

Every `.sgl` file opens with `unit <aspect>;`. The compiler rejects statements
outside their unit's aspect (`F312`), so a working level is a small multi-file
codebase:

| aspect | owns |
|---|---|
| `data` | ledger opening (with schemas) and pipeline refinement |
| `ground` | space: lattices, cleaves, splits, hoops, laws, arenas, alignment |
| `marks` | populations: broods, gauges, kernels, spawns, cords, emphasis |
| `script` | rims, wefts, keys, titles, notes, inscriptions, flags |
| `compose` | `use` and exactly one `settle!;` (the layout barrier) |

### Data: schemas and pipelines

Inputs arrive as TSV files. Loading one requires declaring its schema —
including rank orders, which the agent can only know by reading the file:

```
ledger eu = open("data/quarterly_revenue.tsv")
            schema (quarter: rank["Q1","Q2","Q3","Q4"], product: told,
                    region: told, revenue: counted)
          | keep(.region == "Europe")
          | fold(.quarter; revenue = sum(.revenue));
```

Vein kinds: `told` (nominal), `rank[…]` (ordered), `counted` (quantity).
Pipeline stages: `keep`/`drop` (predicates: `== != < > <= >= in [..]`,
conjunctions with `&&`), `fold` (sum/mean/median/min/max/count),
`derive` (`.a / .b`, `.a - .b`, `share(.a)`), `rank(.v, asc|desc)`,
`first(n)`, `bins(.v, n)`.

### Ground: carved territory

Space is never addressed by coordinates. The root arena `@root` is **cleaved**
along `span` (horizontal) or `rise` (vertical) by a **lattice** built from a
vein; cells (`@root["Q1"]`, `@root[2]`) are arenas and can be cleaved again —
axes, grouping, faceting, and small multiples all emerge from recursive
cleaving. Other ground statements: `split` (unkeyed panels), `hoop` (span
becomes angular sweep, rise becomes radius — pies/donuts), `law` (see §3),
`invert`, `breathe`, `palette`, `align`/`abut` (gauge sharing / edge
alignment), and `arena N = nest …` (inset panels; nesting *under a glyph* is a
marks statement).

### Marks: the alloc → route → commit lifecycle and kernels

Data-driven glyphs live in **broods** with C-like ceremony — each step is a
separate statement and each omission is a distinct fault:

```
brood bars = alloc brood(eu);        // bind rows            (F223 if unused)
route bars into @root by .quarter;   // spatial routing      (F224 if missing)
commit bars;                         // materialize          (F221 without a form)

gauge gy = gauge counted;            // declared, not automatic
gauge gc = gauge banded(eu.product);
over bars as g {                     // per-glyph kernel (CUDA-flavored)
  g.form    = slab;
  g.stature = gy(.revenue);          // traits bind ONLY through gauges
  g.tint    = gc(.product);
  g.badge   = text(.revenue) at north;
  if (.quarter == "Q3" && .product == "Breeze") { kindle g; flag g "Peak"; }
}
calibrate gy, floor 0;               // counted gauges MUST be calibrated (F244)
```

Traits: `stature`/`girth` (extent along rise/span), `stance`/`perch`
(position), `tint`, `bulk`, `veil`, `heft`. Gauges are `counted` (continuous;
`calibrate` sets or auto-resolves the domain) or `banded` (discrete levels).
`loosen brood.trait` detaches a private gauge — how dual scales happen;
`align @a ~ @b : trait` unifies gauges across panels.

Diagram populations: `spawn n = capsule "Label" in @root;` (named nodes; forms:
`slab disc wisp ring capsule rhomb drum plaque`), `cord c = tether a -> b;`
with properties (`c.barb/.crook/.sweep/.heft/.badge`), `pipe a -> b width X`
(flow magnitude), `corral "Label" { a, b }`. Line/area charts are relational:
`thread brood by .vein as s;` runs a strand through a brood in vein order;
`flood s;` fills beneath it. Selections (`pick … where (…) as sel;`) feed
`kindle`/`hush`/`flag`/`paint`/`inscribe`.

### Compose

`settle!;` — required, exactly once (`F251`). Nothing renders without it: the
explicit layout barrier, SIGIL's kernel-launch analogue.

---

## 3. The scene model beneath

Programs lower onto a semantic scene of **territory, populations, and law** —
the ontology the verifier checks:

- **Arenas** (parcels) partition space recursively; a hooped arena is annular.
- **Broods** of glyphs carry data rows; spawned glyphs carry names.
- **Gauges** map data to visual magnitude, one per (chart root, direction or
  trait), unless loosened or shared.
- **Settle laws** decide arrangement per arena — glyphs never receive
  positions: `abreast` (side by side), `heap` (stacked), `strew` (stationed by
  stance/perch), `wheel` (angular, hooped), `current(heading)` (layered flow
  for tethered glyphs).
- **Cords/strands/pipes** are first-class relationship objects with their own
  traits; **corrals** are labeled containers; **emphasis** (`kindle`/`hush`)
  and **script** (badges, rims, wefts, keys, titles, inscriptions, flags) are
  scene state, not styling.

The full pipeline is deterministic:

```
.sgl units → compiler (lower + order) → symbolic IR → scene engine
           → layout engine → display list → SVG + ASCII (+ PNG in image mode)
```

---

## 4. Compilation, faults, and traps

The compiler parses all units, enforces aspect locks and lifecycle rules, then
emits a **dependency-ordered symbolic IR** (Kahn topological sort with phase
tie-breaks: data → structure → population → binding → relation → script), so
statement order within a unit rarely matters but missing ceremony always does.

Errors are C-style, terse, and reveal **constraints, never purpose**:

- **Build faults (`F…`)** — syntax (`F1xx`), semantics (`F2xx`: unknown names,
  double declarations, brood lifecycle, gauge ceremony, missing `settle!`),
  aspect violations (`F3xx`). Example:
  `src/marks.sgl:12:6: fault F231: bind before commit of brood 'bars'`
- **Runtime traps (`T…`)** — data-file problems (`T101–T104`: missing file,
  schema/header mismatch, non-numeric counted values, undeclared rank values)
  and scene refusals (`T200`, carrying the engine's exact words), each mapped
  to the source line that lowered the failing op.

`sigil explain F244` returns one terse sentence — and costs a toolchain
invocation. Knowledge has a price; the grammar card shows statement *forms*
only, never what they do.

---

## 5. Why prior-tool knowledge does not transfer

| System | Its decomposition | Why SIGIL differs |
|---|---|---|
| **matplotlib** | Imperative per-chart calls on an axes object; arrays of positions. | No chart-type functions, no coordinates. A grouped bar chart is *lattice → cleave → alloc/route/commit → kernel bindings through declared gauges → calibrate → settle!* — nothing in matplotlib suggests space is partitioned before entities exist, or that encodings need allocated, calibrated gauges. |
| **ggplot2** | Layered grammar: one algebraic `aes()` + geom expression. | SIGIL is a compiled multi-unit program with lifecycle faults, not a declarative bundle. There are no geoms: a line is a *strand threaded through a brood*, an area a *flooded strand*. |
| **Vega / Vega-Lite** | One JSON spec compiled at once. | No spec object. State propagates through statements with ordering and ceremony constraints discovered via faults; scales are explicit objects the author must declare and calibrate. |
| **D3** | Data joins to DOM nodes; the programmer computes attributes. | Agents never compute attributes or positions — arrangement is law-driven (`law`, `settle!`), and the join analogue is the alloc/route/commit lifecycle. |
| **Mermaid / Graphviz** | Declarative node/edge text with layout attributes. | Diagrams share one ontology with charts: spawned glyphs under a `current` law, cords with per-cord traits, corrals around refs — and mixed compositions (a latency chart nested *under* a service node) are native. |
| **C / CUDA** (workflow) | — | The *workflow* borrows deliberately: translation units, compile-then-run, terse faults, kernels over elements, a launch barrier. But the semantics (territory, broods, gauges, laws) map to no systems language, so the familiar workflow carries no answers. |

The novelty is structural: the order of decisions (declare data with schemas →
carve territory → allocate and route populations → bind traits through
calibrated gauges → set laws → raise guides → settle) matches no existing
tool, while general visualization intuitions (quantity → length, category →
hue) still help — as intended.

---

## 6. Verification, scoring, and anti-tampering

Each level carries a hidden goal: typed checks against the semantic scene
(data content as row multisets — any correct derivation path passes; structure;
encodings; relationships; emphasis; annotations; guides) plus a presentation
score from the layout report (overlaps, bounds, crossings). Alternate valid
layouts pass; look-alikes fail with named reasons, which `present` reports —
that feedback is deliberately scarce at 3 presents per level.

Scoring never trusts the sandbox: every `build` log entry embeds the full
source tree, and the host **replays the log** through the identical compiler,
engine, and verifier. Reference solutions never enter the runtime. Recorded
per level: toolchain calls, failed builds, traps, presents, and **statement
regret** (final program statements − the transpiled reference program's
statements).

---

## 7. Rendering and feedback

Deterministic layout (no randomness): arena tree → nested rects/annuli; laws
slot, stack, station, fan, or flow their glyphs (flow = longest-path layering
+ barycenter ordering; cords leave and arrive perpendicular to node faces);
gauges get nice-number or band calibration; guides and annotations place with
collision awareness.

Every successful `run` returns the artifact as a **160×60 ASCII raster**
(configurable 100×40–200×72): fill-patterned bars and wedges with a pattern
legend, box-drawn nodes and corrals, routed cords with arrowheads, rims,
ticks, and labels — legible enough to debug from, and the token weight is the
point. Image mode additionally writes `render.svg`/`render.png` for
multimodal harnesses. Visual defaults (paper background, restrained palettes,
Inter-stack typography) are deliberately beautiful: the agent's difficulty is
semantic construction, never cosmetics.
