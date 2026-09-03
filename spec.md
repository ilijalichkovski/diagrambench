Build a benchmark prototype for lifelong/continual learning called **DiagramBench**.

## Core idea

DiagramBench is a persistent interactive environment in which an LLM agent must learn, through experience, how to use a **completely novel plotting and diagramming SDK**.

The SDK should be capable of producing beautiful:

* bar charts
* line charts
* area charts
* scatter plots
* histograms
* pie/donut charts
* grouped/stacked charts
* flowcharts
* architecture diagrams
* node/edge diagrams
* hierarchical diagrams
* timelines
* process diagrams
* mixed chart + diagram compositions
* annotated visual explanations

The benchmark is deliberately designed so that the LLM **cannot rely on prior knowledge of matplotlib, Vega, D3, Mermaid, Graphviz, ggplot, Plotly, SVG, HTML/CSS, etc.**

The API must therefore be genuinely novel in:

* terminology
* abstractions
* decomposition of operations
* parameterization
* object model
* composition model

Do NOT simply rename existing library functions.

The benchmark tests whether an agent can:

1. discover an unknown tool through interaction,
2. retain what it learns over a long lifetime,
3. reuse previously discovered primitives,
4. compose them in increasingly sophisticated ways,
5. develop higher-level understanding of the SDK,
6. solve novel tasks increasingly efficiently.

The benchmark should feel like:

> A novice designer is handed a strange but powerful visualization instrument. Over thousands of tasks, they gradually become a master of it.

The human-facing visualization is important.

Every task should produce a clean, minimal, attractive visual artifact, and users should be able to watch the agent’s attempts improve.

---

# 1. Environment structure

There is ONE SDK for the entire lifetime.

The SDK never resets or changes.

The agent receives a sequence:

τ₁, τ₂, τ₃, ..., τₙ

of visualization tasks.

Each task:

* starts with an empty canvas or partially constructed artifact,
* has a textual specification,
* has a hidden semantic ground truth,
* has one or more valid visual solutions,
* can be solved using the SDK,
* is automatically verifiable.

The agent interacts with the SDK entirely through text/tool calls.

Humans see the rendered artifact after every meaningful action.

Example human experience:

Task:
“Show quarterly revenue for three products as grouped bars. Highlight Product B in Q3 and annotate that quarter as the peak.”

Attempt 1:
wrong grouping, wrong axis

Attempt 2:
correct bars, wrong grouping

Attempt 3:
correct grouping and colors

Attempt 4:
correct annotation

SUCCESS

The progression should be satisfying to watch.

---

# 2. SDK design

Design an SDK with roughly **80–150 meaningful primitives / operations / modifiers**.

However, these should be generated from perhaps **15–30 deeper conceptual families**.

The API must be internally coherent.

The agent should eventually be able to infer its grammar.

Examples of conceptual families might include:

* creating visual entities
* binding information to visual properties
* grouping
* repetition
* aggregation
* spatial arrangement
* relationships
* containment
* ordering
* geometric constraints
* alignment
* routing
* scaling
* filtering
* transformation
* labeling
* annotation
* emphasis
* layering
* coordinate systems
* styling
* legends
* axes
* layout optimization

But DO NOT expose these abstractions using terminology from known visualization libraries.

Invent a genuinely new worldview.

For example, rather than:

```
chart.bar(x="month", y="sales")
```

the SDK might conceptually treat visualization as something like:

```
field("sales_data")
cast("month", onto="march")
lift("sales", through="height")
repeat(by="product")
settle(mode="columns")
```

This example is ONLY illustrative.

Invent something much better and internally consistent.

Important:

### Do not make novelty purely lexical.

BAD:

```
matplotlib.bar() -> glorp()
```

GOOD:

The API decomposes visualization construction differently enough that knowing matplotlib does not immediately reveal the solution.

The model should have to learn:

* what objects exist,
* how state propagates,
* which operations modify what,
* which concepts compose,
* which defaults exist,
* ordering constraints,
* interactions between primitives.

---

# 3. API discovery

The agent does NOT receive full documentation.

At the beginning it knows only a tiny bootstrap interface.

For example:

```
catalog()
probe(...)
invoke(...)
inspect(...)
undo()
reset_task()
```

Exact naming is up to you.

The bootstrap interface should permit discovery without revealing semantics.

The agent should be able to discover:

### Available operation names

Example:

```
catalog("composition")

> weave
> nest
> tether
> settle
> frame
```

### Signatures

Example:

```
probe("weave")

weave(source, key, mode?)
```

But NOT:

> “weave groups data by a categorical field.”

### Weak type information

Example:

```
source: collection
key: field
mode: enum
```

### Informative error messages

Errors should reveal syntax and constraints but not full semantics.

GOOD:

```
Error: weave requires a discrete key.
Received continuous field "revenue".
```

BAD:

```
weave groups marks by category. Use it to create grouped charts.
```

### Consequence inspection

After calling an operation, the agent receives:

* textual state changes,
* perhaps a concise description of entities now present,
* access to inspect generated structures.

Example:

```
invoke(...)

Result:
12 visual units created.
3 bands now occupy the horizontal field.
```

The rendered artifact is visible to humans but SHOULD NOT be necessary for the language-only agent.

Everything needed to solve the benchmark must be available through textual observations.

---

# 4. Separate agent view from human view

This is critical.

## Agent view

Purely textual.

Example:

```
CANVAS
entities: 12
groups: 3
relationships: 0

ENTITY SUMMARY
e1-e4: family=A
e5-e8: family=B
e9-e12: family=C

LAYOUT
horizontal occupancy: 0.81
vertical occupancy: 0.63

WARNINGS
- 4 labels overlap
- legend not present
```

The agent may inspect more detail explicitly.

## Human view

Render a gorgeous visualization.

Use a minimalist visual language:

* white/light neutral backgrounds
* excellent typography
* restrained palette
* strong spacing
* clean axes
* subtle gridlines
* elegant labels
* smooth transitions
* no default ugly browser styling

Think high-end editorial / Observable / Stripe / Linear quality.

The benchmark should look impressive in demos.

Every agent action that meaningfully changes the visual should animate smoothly.

Examples:

* bars grow/shrink
* nodes rearrange
* edges reroute
* labels fade/reposition
* sections regroup
* annotations appear
* pie wedges morph
* layouts settle
* colors interpolate

Watching a task being solved should be satisfying even if the viewer knows nothing about ML.

---

# 5. Internal representation

Do NOT score screenshots directly as the primary verifier.

Every rendered artifact should correspond to a canonical internal semantic representation.

Suggested architecture:

```
Agent API calls
      ↓
DiagramBench semantic scene
      ↓
layout engine
      ↓
SVG renderer
```

The semantic scene should contain concepts such as:

* entities / marks
* data bindings
* groups
* edges / relationships
* hierarchy
* scales
* transforms
* constraints
* annotations
* layout intentions
* styles

The exact ontology should follow the novel SDK design.

SVG is probably the easiest rendering target.

Keep rendering deterministic.

---

# 6. Verification

Each task should be generated from a hidden semantic specification.

For example:

```
DATA:
quarter, product, revenue

SEMANTIC GOAL:
filter region == Europe
aggregate revenue by quarter/product
display grouped comparison
quarter → horizontal progression
revenue → magnitude
product → identity
emphasize Product B in Q3
annotate max point
include legend
```

The task presented to the agent might be:

> Create a grouped bar chart showing quarterly European revenue for each product. Make Product B's Q3 bar stand out and label it “Peak quarter”.

The verifier should inspect the candidate semantic scene.

Use several levels of correctness.

## A. Semantic correctness — dominant component

Check:

* correct data
* correct filters
* correct aggregations
* correct marks/entities
* correct relationships
* correct encodings
* correct grouping
* correct hierarchy
* correct annotation semantics
* correct requested labels
* correct directional flow
* correct chart/diagram meaning

This should account for ~80–90% of success.

## B. Presentation constraints

Check:

* no major overlaps
* labels legible
* diagram edges readable
* requested orientation respected
* content within bounds
* reasonable whitespace
* visual hierarchy respected
* required legend/axes shown
* edge crossings minimized where applicable

Do NOT require exact pixel equivalence.

Multiple layouts should be valid.

## C. Efficiency

Record:

* total API calls
* failed calls
* introspection calls
* undo calls
* token usage
* wall-clock/environment steps

Do not necessarily make efficiency part of pass/fail initially.

Track it as regret.

---

# 7. Regret

For every task, because the hidden generator knows a valid construction program P*, record its semantic action length.

Let:

C_agent = number of environment actions used by the agent
C_ref = reference construction cost

Define simple action regret:

R = C_agent - C_ref

Do not claim C_ref is globally optimal unless an actual planner proves this.

Initially call this “reference regret” if needed.

Over the lifetime we want to see:

R_t ↓

especially for primitives the agent has already encountered.

This is analogous to TaxiBench:

* novice explores inefficiently,
* expert navigates the instrument efficiently.

---

# 8. Curriculum

Create an initial curriculum of approximately **200 tasks**.

Make it explicitly staged.

Do NOT randomize everything.

We want a pedagogically meaningful progression that makes lifelong learning visible.

## Stage 1 — primitive discovery

Tasks ~1–25

Each task mostly isolates ONE new primitive or concept.

Examples:

* create a single labeled quantity
* make two objects
* arrange objects horizontally
* connect A to B
* display categories as repeated shapes
* map magnitude to size
* attach a label
* introduce grouping
* simple bar chart
* simple node-edge diagram

Each task should be tiny.

The purpose is to let the agent perform scientific experimentation on the SDK.

Later tasks should reuse these primitives.

## Stage 2 — short compositions

Tasks ~26–60

Require combinations of 2–4 previously encountered primitives.

Examples:

* grouped bar chart
* basic pie chart with labels
* simple flowchart
* two-level hierarchy
* line chart with annotation
* scatter plot with category grouping

Occasionally introduce one new primitive in a task largely solvable with familiar ones.

## Stage 3 — medium compositions

Tasks ~61–110

Require 4–8 concepts.

Examples:

* stacked chart with ordering and labels
* annotated timeline
* architecture diagram with groups and directional flows
* multi-series line chart with reference line
* process diagram with branching
* scatter plot with encoded size/color and annotation
* combined bar + line visualization

## Stage 4 — advanced composition

Tasks ~111–160

Require perhaps 8–15 concepts.

Introduce:

* nested groups
* mixed visual grammars
* multiple coordinated panels
* nontrivial annotations
* advanced edge routing
* derived data
* several transformations
* alignment constraints
* semantic emphasis

Tasks should now look like realistic visuals someone might put into a report.

## Stage 5 — mastery

Tasks ~161–200

Complex, polished compositions.

Require solid knowledge of the SDK.

Examples:

### Example A

“Create an architecture diagram showing:
users → gateway → three services.
Group the services as ‘Core’.
Payments and Orders share a database.
Search uses a separate vector store.
Use left-to-right flow.
Highlight the Payments path.
Include a small latency bar chart beneath each service.”

This combines diagramming + charting.

### Example B

“Show monthly revenue and operating margin across 24 months. Revenue should be bars, margin a line using a separate scale. Highlight the period after launch, annotate the highest-margin month, and add a compact breakdown of revenue by product for the final month.”

### Example C

“Visualize a hiring funnel as a flow diagram from Applicants → Screen → Interview → Offer → Hired, with widths proportional to candidate counts. Beside each stage, show the median time spent there. Highlight the stage with the largest loss.”

These should be visually impressive.

---

# 9. Curriculum principles

Very important:

The curriculum should create opportunities to measure:

### Reuse

Does encountering primitive X once make future X tasks cheaper?

### Composition

Can primitives learned independently be composed for the first time?

Example:

* agent learned grouping
* agent learned annotation
* agent learned bar charts

Then gets first-ever:

* grouped annotated bar chart

### Increasing composition depth

Track approximate required primitive count per task.

Plot lifetime step vs required composition depth.

### Systematic generalization

Expose related API operations.

Example:
agent learns one member of an operation family.

Later introduce another operation from the same family.

Does discovery become faster?

### Retention

Reintroduce primitives after long gaps.

### Plasticity

Late in the curriculum, introduce genuinely new primitives.

Measure whether the old agent can learn them as efficiently as it learned primitives early in life.

This is important for eventual lifelong-RL experiments.

---

# 10. Task generation

For the prototype, manually author the 200-task curriculum as structured specs.

But design the system so that later we can generate unlimited tasks programmatically.

Every task should be represented as something like:

```json
{
  "id": "...",
  "stage": 3,
  "instruction": "...",
  "dataset": "...",
  "hidden_goal": {...},
  "reference_program": [...],
  "required_concepts": [...],
  "new_concepts": [...],
  "difficulty": {...}
}
```

The agent must NEVER see:

* hidden_goal
* reference_program
* required_concepts
* new_concepts

These are evaluator metadata.

---

# 11. Datasets

Bundle several small synthetic datasets suitable for charts.

Examples:

* company revenue
* product metrics
* website traffic
* experiment results
* survey responses
* population data
* model evaluation results
* hiring funnel
* latency metrics
* sales pipeline

Data should be deterministic.

Avoid huge datasets.

The challenge is learning the SDK, not data wrangling scale.

Diagram tasks generally do not need datasets; their graph structure can be generated directly.

---

# 12. Visual quality

Treat this as a first-class requirement.

Rendered outputs should look beautiful by default.

The agent should not need to spend 20 actions fixing ugly defaults.

Choose good defaults for:

* typography
* padding
* axes
* gridlines
* node shapes
* edge styles
* arrowheads
* palette
* annotation styling
* legends
* label spacing

The difficulty should come from semantic construction and composition, NOT manually tuning RGB values or pixel positions.

An expert solution should look presentation-ready.

Use smooth SVG animations between scene states.

The UI should show:

LEFT:
task instruction

CENTER:
large rendered canvas

RIGHT:
agent textual interaction log / current semantic status

TOP/BOTTOM:

* task number
* stage
* success
* actions
* reference regret
* lifetime cumulative stats

---

# 13. SDK requirements

Before writing lots of curriculum tasks, first design the SDK carefully.

Produce a standalone document:

`docs/sdk-design.md`

It should explain internally:

* conceptual model
* all operation families
* operation names
* signatures
* object lifecycle
* state model
* composition semantics
* error semantics
* introspection API
* rendering mapping

This documentation is for benchmark developers ONLY.

The benchmark agent must not see it.

Explicitly compare the proposed SDK against:

* matplotlib
* ggplot
* Vega/Vega-Lite
* D3
* Plotly
* Mermaid
* Graphviz

and explain why knowledge of those systems does NOT trivially transfer.

If the design is just renamed Vega or D3, redesign it.

---

# 14. Prototype deliverables

Build a runnable local prototype.

Suggested stack:

* Python environment/backend
* browser frontend
* SVG renderer
* deterministic state
* simple HTTP/WebSocket or local server
* clean separation between SDK semantics and renderer

But choose whatever stack makes implementation fastest and cleanest.

Deliver:

1. `README.md`

   * what DiagramBench is
   * screenshots/examples
   * how to run it

2. `docs/sdk-design.md`

3. SDK implementation

4. semantic scene representation

5. SVG renderer

6. textual agent interface

7. discovery/introspection interface

8. verifier

9. task schema

10. first 200 curriculum tasks

11. curriculum metadata

12. human-facing benchmark viewer

13. logging:

* action history
* success
* semantic score
* layout score
* reference regret
* per-primitive exposure history

14. scripted random-agent/demo-agent support

---

# 15. Milestone order

Do NOT attempt all 200 tasks first.

Build in this order.

### Milestone 1

Design the SDK.

Do not code until the API feels genuinely novel and coherent.

### Milestone 2

Implement semantic scene + renderer.

Manually build:

* one bar chart
* one pie chart
* one line chart
* one flowchart
* one architecture diagram

using the SDK.

Verify they look excellent.

### Milestone 3

Implement textual interaction + discovery.

Demonstrate a fresh agent could experimentally infer one primitive.

### Milestone 4

Implement semantic verifier.

Show that:

* alternate valid layouts pass,
* semantically incorrect but visually similar artifacts fail.

### Milestone 5

Author first ~25 primitive-discovery tasks.

### Milestone 6

Expand to ~60 composition tasks.

### Milestone 7

Complete 200-task curriculum.

### Milestone 8

Polish animations and benchmark viewer.

---

# 16. Important anti-goals

Do NOT:

* expose matplotlib/D3/Vega/etc.
* make this a thin wrapper around an existing plotting API
* make command names arbitrary nonsense like `zorp()` merely for novelty
* require visual input from the agent
* rely on an LLM judge for core correctness
* use screenshot similarity as primary verification
* require exact pixel matching
* make styling the main challenge
* generate ugly default charts
* give the agent the SDK manual
* make every task IID
* introduce every primitive immediately
* reset agent knowledge between tasks
* conflate exploration actions with task failure

---

# 17. Benchmark philosophy

This is not primarily a visualization benchmark.

It is a **lifelong tool-learning benchmark**.

Visualization is chosen because:

1. humans immediately understand whether the agent is getting closer,
2. outputs can be beautiful and satisfying to watch,
3. the underlying tool can be extremely compositional,
4. tasks can scale from trivial to extremely complex,
5. correctness can be verified structurally,
6. plotting/diagramming is a realistic LLM-agent use case.

The central scientific question is:

> If an agent interacts with the same complicated tool for its entire lifetime, does it gradually become an expert?

Eventually we want to compare:

* context-only agents
* note-taking agents
* retrieval/memory systems
* weight-updated agents
* continual RL algorithms
* algorithms designed to avoid loss of plasticity

The benchmark therefore needs detailed lifetime traces.

We should eventually be able to plot:

```
task number
    vs
task success

task number
    vs
reference regret

task number
    vs
API discovery cost

task number
    vs
composition depth solved

task number
    vs
learning speed on newly introduced primitives
```

A good lifelong learner should show the unmistakable trajectory:

**confused novice → competent user → fluent expert → master of the instrument.**

Build the prototype around making that trajectory measurable and visually obvious.