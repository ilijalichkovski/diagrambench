# VELD — the DiagramBench SDK (developer documentation)

> **This document is for benchmark developers only. The agent must never see it.**
> The agent gets only the bootstrap interface (`families`, `ops`, `sig`, `forms`,
> `shelf`, `peek`, `census`, `study`, `undo`, `restart`, `present`) and must infer
> everything else through interaction.

VELD is the single, persistent visualization instrument at the heart of DiagramBench.
The agent lives with it for its entire lifetime; it never resets or changes.

---

## 1. Conceptual model

VELD does not think in "charts". It thinks in **territory, populations, and law**:

1. **The ground.** Every task begins with a blank rectangular **ground** holding a
   single root **parcel** (`p0`). Parcels are territories. Space is never addressed
   by pixels or coordinates — it is **carved**: a parcel can be split along one of
   its two directions (**span** = horizontal, **rise** = vertical) into cells keyed
   by the values of a data column. Cells are themselves parcels and can be carved
   again. All classical "axes", "grouping", "faceting", and "small multiples"
   emerge from recursive carving.

2. **Ledgers and veins.** Data lives in **ledgers** (small named tables). A column
   of a ledger is a **vein**. Veins have *kinds*: `told` (nominal categories),
   `ranked` (ordered categories, e.g. months), `counted` (quantities). New ledgers
   are produced by refinement operations (`sift`, `distill`, `bin`, `derive`,
   `marshal`, `crop`) which record provenance.

3. **Glyphs, broods, sowing.** Visual entities are **glyphs**. Data-driven glyphs
   are created in a **brood** — one glyph per ledger row — by **sowing** a ledger
   into a parcel. Sowing into a carved parcel requires a `key` vein that routes
   each glyph to its cell. Standalone glyphs (diagram nodes) are **placed**
   individually and can be given names.

4. **Metering.** A glyph has **traits**: `stature` (extent along rise), `girth`
   (extent along span), `stance` (position along span), `perch` (position along
   rise), `tint` (color), `bulk` (overall size), `veil` (opacity). Data becomes
   visible by **metering** a brood: `meter(brood, trait, vein)` routes a vein's
   values into a trait through an automatically managed **gauge** (a calibrated
   mapping owned by the parcel). Gauges can be re-based, shared, or **loosened**
   (detached to an independent gauge — how dual scales happen).

5. **Settling.** Glyphs never receive positions. Each parcel has a **settle law**
   deciding how the glyphs inside each cell arrange themselves:
   `abreast` (side by side), `heap` (piled on top of one another), `strew`
   (positioned by stance/perch meterings), `wheel` (angular, in hooped parcels),
   `current` (flow layout for tethered glyphs, with a compass `heading`).

6. **Hooping.** A parcel may be **hooped**: its span direction becomes angular
   sweep and its rise becomes radius. Pie/donut charts are hooped parcels whose
   glyph girths are normalized by the `wheel` law. `inner` reserves a hole.

7. **Cords.** Relationships are **cords**: `tether(a, b)` connects two glyphs
   (directed by default, arrow at head). `thread(brood, by)` runs a single
   **strand** through a brood in vein order (this is how line charts exist);
   `flood(strand)` fills beneath it (area charts); `pipe(a, b, width)` is a cord
   with magnitude (flow/funnel diagrams). Cords have their own traits
   (`heft`, `barb`, `sweep`, `crook`).

8. **Bands.** `flock` builds a named selection of glyphs; `pick` selects glyphs
   from a brood by data predicate; `corral` draws a labeled container around
   members (architecture groupings).

9. **Script & guides.** `badge` (labels on glyphs, fixed text or vein-driven),
   `inscribe` (free annotation anchored near a target), `flag` (callout with a
   leader line), `entitle`/`note` (title/caption), `rim` (calibrated edge showing
   a gauge — the axis analogue), `weft` (faint gridlines), `key` (legend of a
   tint/bulk metering).

10. **Emphasis & layers.** `kindle` (highlight), `hush` (de-emphasize),
    `lift`/`sink` (stacking order).

11. **Patina.** Fixed styling: `tint`, `veil`, `outline`, `palette`. Defaults are
    deliberately beautiful; patina is rarely required for correctness.

Everything renders through a deterministic pipeline:

```
agent op calls → semantic scene → layout engine → display list → SVG (+ animation)
```

The verifier only ever reads the semantic scene, never pixels.

---

## 2. Why prior-library knowledge does not transfer

| System | Its decomposition | Why VELD differs |
|---|---|---|
| **matplotlib** | Imperative per-chart functions (`bar`, `plot`, `pie`) on an axes object; positions/sizes passed as arrays. | VELD has no chart-type functions and no coordinate arguments. A bar chart is *carve → sow → meter stature*; nothing in matplotlib suggests that space must be partitioned before entities exist. |
| **ggplot2** | Layered grammar: `aes()` mappings + geoms + stats + facets declared in one algebraic expression. | VELD is stateful and sequential; "faceting" and "x position" are the same primitive (carving), and encodings are per-brood mutations, not a declarative bundle. There are no geoms: a line is a *strand threaded through a brood*, an area is a *flooded strand*. |
| **Vega / Vega-Lite** | JSON spec: marks + encoding channels + scales + transforms compiled at once. | No spec object exists. State propagates through ops with ordering constraints (sow before meter; carve before keyed sow; hoop changes the meaning of girth). Scales (gauges) are side effects owned by parcels, discovered via errors and `study`. |
| **D3** | Data joins binding rows to DOM nodes; explicit scales; the programmer computes attributes. | Agents never compute attributes or positions. The join analogue (sowing) is one op, and layout is entirely law-driven (`settle`), not attribute-driven. |
| **Plotly** | Trace objects per chart type with a `layout` dict. | No traces, no layout dict. Composition is spatial (nest/carve) and relational (cords), not a list of traces. |
| **Mermaid** | Text DSL declaring nodes/edges with chart-type headers. | Diagrams are built by placing glyphs and tethering them under a `current` law, in the *same* ontology as charts — mixed chart/diagram composition is native (`nest` a parcel under a placed glyph and sow bars into it). Mermaid knowledge suggests none of that. |
| **Graphviz** | Declarative dot graph + global layout attributes. | Cords are first-class scene objects with per-cord traits; routing is a per-cord `crook`; grouping is `corral` around glyph refs, not subgraph syntax. |

The novelty is structural, not lexical: the *order of decisions* an agent must make
(carve space → populate → meter → settle → guide) does not match any of the above,
so knowing them does not reveal solutions — though general visualization concepts
(quantity → length, category → hue) still help, as intended.

---

## 3. Object model & lifecycle

Refs are short ids handed out by ops: `p#` parcel, `b#` brood, `g#` glyph,
`c#` cord, `s#` strand, `f#` flock, `L#` derived ledger, `k#` corral, `a#`
annotation. Base ledgers are addressed by name (from `shelf()`).

Lifecycle rules (enforced; violations produce instructive errors):

- A parcel can be carved once (`undo` or `nest` to go further). Carving a parcel
  that already hosts sown broods is refused.
- `sow` into a carved parcel requires `key=` (a vein of the sown ledger whose
  values match the carve keys). Sowing into an uncarved parcel pools all glyphs
  in the single implicit cell.
- `meter` requires trait/vein kind agreement: `stature`, `girth`, `perch`,
  `stance`, `bulk`, `veil`, `heft` need `counted` veins (exception: `stance`/
  `perch` accept `ranked`/`told` veins, producing a stationed gauge); `tint`
  accepts `told`/`ranked` (palette) or `counted` (ramp).
- `settle("strew")` requires at least one of stance/perch metered.
  `thread` requires an ordering vein. `flood` requires a strand.
- `hoop` must precede sowing in that parcel. In a hooped parcel `girth` means
  angular share and the default law is `wheel`.
- `tether`/`pipe` require glyph refs (or names of placed glyphs).
- `settle("current", heading=…)` applies to parcels whose glyphs are placed;
  tethers determine ordering (layered flow layout).
- One gauge per (parcel, direction-or-trait); `loosen` gives a brood a private
  gauge; `share` unifies gauges across parcels (aligned panels).

State model: the scene is a persistent object per task; every mutating op pushes
an undo snapshot. `restart` clears the task's scene. `present` submits the scene
for verification.

---

## 4. Operation families and signatures

Weak-typed signatures exactly as `sig()` reveals them. `?` marks optional.

### family `ledgers` (data refinement)
| op | signature |
|---|---|
| `shelf` | `shelf()` → names & sizes of base ledgers |
| `peek` | `peek(ledger, rows?)` → first rows |
| `veins` | `veins(ledger)` → vein names & kinds |
| `sift` | `sift(ledger, vein, relation, value)` → ledger. relation ∈ `is,is_not,above,below,at_least,at_most,among` |
| `distill` | `distill(ledger, by, take, mode)` → ledger. mode ∈ `sum,mean,median,min,max,count` |
| `derive` | `derive(ledger, name, mode, a, b?)` → ledger. mode ∈ `ratio,diff,total_share` |
| `bin` | `bin(ledger, vein, bins?)` → ledger with `bin`,`tally` |
| `marshal` | `marshal(ledger, vein, sense)` → ledger. sense ∈ `waxing,waning` |
| `crop` | `crop(ledger, first)` → ledger |

### family `ground` (space)
| op | signature |
|---|---|
| `carve` | `carve(parcel, along, ledger, by, gap?)` along ∈ `span,rise` |
| `split` | `split(parcel, along, count, gap?)` → equal unkeyed cells (panels) |
| `cell` | `cell(parcel, at)` → parcel ref of a carve/split cell |
| `nest` | `nest(parcel?, host?, aim?, breadth?, depth?)` → inset parcel (in a parcel or under a glyph) |
| `hoop` | `hoop(parcel, inner?)` |
| `breathe` | `breathe(parcel, amount)` padding 0..1 |
| `invert` | `invert(parcel, along)` reverse direction |
| `abut` | `abut(parcel_a, parcel_b, edge)` alignment constraint |

### family `sowing` (entity creation)
| op | signature |
|---|---|
| `sow` | `sow(parcel, ledger, form, key?)` → brood |
| `place` | `place(parcel, form, name?)` → glyph |

Forms (from `forms()`): `slab` (block; wedge when hooped), `disc`, `wisp`
(small point), `ring`, `capsule` (rounded card, auto-badged with its name),
`rhomb` (decision), `drum` (store/database), `plaque` (text card).

### family `metering`
| op | signature |
|---|---|
| `meter` | `meter(brood, trait, vein)` |
| `rebase` | `rebase(parcel, trait, floor?, ceil?)` set gauge domain |
| `loosen` | `loosen(brood, trait)` detach onto private gauge |
| `share` | `share(parcel_a, parcel_b, trait)` unify gauges |
| `unmeter` | `unmeter(brood, trait)` |

### family `settling`
| op | signature |
|---|---|
| `settle` | `settle(parcel, law, heading?)` law ∈ `abreast,heap,strew,wheel,current`; heading ∈ `east,west,north,south` |

### family `cords`
| op | signature |
|---|---|
| `tether` | `tether(tail, head, sense?)` sense ∈ `forth,both` → cord |
| `thread` | `thread(brood, by)` → strand |
| `flood` | `flood(strand)` |
| `pipe` | `pipe(tail, head, width)` width = number or vein value → cord |
| `barb` | `barb(cord, at)` at ∈ `head,tail,both,none` |
| `sweep` | `sweep(cord, amount)` curvature −1..1 |
| `crook` | `crook(cord, style)` style ∈ `straight,bend,arc` |
| `heft` | `heft(cord_or_strand, weight)` thickness 0..1 |

### family `bands`
| op | signature |
|---|---|
| `flock` | `flock(members, name?)` → flock |
| `pick` | `pick(brood, vein, relation, value)` → flock |
| `corral` | `corral(members, label?)` → corral |
| `disband` | `disband(flock_or_corral)` |

### family `script`
| op | signature |
|---|---|
| `badge` | `badge(target, text?, vein?, aim?)` aim ∈ `auto,north,south,east,west,center,rim` |
| `inscribe` | `inscribe(text, near?, aim?)` → annotation |
| `flag` | `flag(target, text)` → callout annotation |
| `entitle` | `entitle(parcel, text)` |
| `note` | `note(parcel, text)` |

### family `guides`
| op | signature |
|---|---|
| `rim` | `rim(parcel, side)` side ∈ `south,west,north,east` (east binds a loosened rise gauge if present) |
| `weft` | `weft(parcel, along)` gridlines |
| `key` | `key(parcel, brood, trait)` legend |

### family `emphasis`
| op | signature |
|---|---|
| `kindle` | `kindle(target)` |
| `hush` | `hush(target)` |

### family `layers`
| op | signature |
|---|---|
| `lift` | `lift(target)` |
| `sink` | `sink(target)` |

### family `patina`
| op | signature |
|---|---|
| `tint` | `tint(target, hue)` hue ∈ named tokens (`ember,tide,moss,plum,sand,slate,rose,teal,ink,mist`) |
| `veil` | `veil(target, amount)` |
| `outline` | `outline(target, weight)` |
| `palette` | `palette(parcel, name)` name ∈ `quill,dusk,field,ember` |

### family `oracle` (introspection — bootstrap)
`families()`, `ops(family)`, `sig(op)`, `forms()`, `census()`, `study(ref)`,
`trace()`.

### family `helm` (control — bootstrap)
`undo()`, `restart()`, `present()`.

Counting primitives: 63 ops + 8 forms + 8 traits + 5 laws + 7 sift relations
+ 6 distill modes + 3 derive modes + 4 headings + 4 sides + 7 aims + 4
palettes ≈ **119 meaningful primitives** drawn from **14 conceptual
families** — within the spec's 80–150 primitive / 15–30 family targets.

---

## 5. Error semantics

Errors reveal **syntax and constraints, never purpose**. Patterns:

- Arity/type: `` sow: unknown argument 'colour'. Accepted: parcel, ledger, form, key. ``
- Kind mismatch: `` meter: trait 'stature' requires a counted vein; 'product' is told. ``
- Ordering: `` sow: parcel p0 is carved by 'quarter'; provide key= to route glyphs. ``
- Enum: `` settle: unknown law 'grid'. Laws: abreast, heap, strew, wheel, current. ``
- Missing state: `` thread: brood b1 has no metering along rise; strand would be flat. `` (warning, not error)

Never emitted: "use X to build a grouped bar chart" or any purpose-revealing text.

---

## 6. Introspection / observation model

After every op the agent receives a short textual consequence, e.g.

```
b1: 12 glyphs sown into p0 (4 cells by 'quarter', 3 per cell).
```

`census()` prints the standard agent view (entities, parcels & laws, meterings,
cords, guides, warnings). `study(ref)` gives per-object detail, including gauge
calibration, cell membership, provenance of derived ledgers, and cord topology.
Everything the verifier can see is reachable textually; the rendered SVG is for
humans only.

---

## 7. Rendering mapping

Deterministic layout engine, no randomness:

- Parcel tree → nested rects (gaps, breathing, hoop → annulus).
- `abreast`/`heap` → slotting within cells; `strew` → gauge-resolved stations;
  `wheel` → normalized angular spans; `current` → layered flow layout
  (longest-path layering, barycenter ordering, orthogonal-ish cord routing).
- Gauges → nice-number calibration for counted veins; band calibration for
  told/ranked.
- Guides, badges, annotations placed with collision-aware anchoring.
- Output: a **display list** of stable-id primitives; the viewer tweens numeric
  attributes between successive display lists, so every meaningful change
  animates (bars grow, wedges morph, nodes glide, labels fade).

Visual defaults: light paper background, Inter/system typography, restrained
palettes, hairline gridlines, generous whitespace. Beauty is the default; the
agent's difficulty is semantic, never cosmetic.
