# diagrambench-v1 (SIGIL edition)

DiagramBench as a native verifiers v1 environment. One rollout is one
*lifetime*: the agent must master **SIGIL** — an unfamiliar compiled language
for constructing visual artifacts — across curriculum levels that unlock
**strictly in order**. Each level is a small **multi-file project** in its own
sandboxed folder, with task inputs shipped as data files.

## The loop

```
levels/L001/
├── BRIEF.md            the instruction
├── sigil.toml          project manifest
├── data/*.tsv          inputs (schemas must be declared to load them)
├── src/*.sgl           the agent's units — `unit data|ground|marks|script|compose;`
└── out/render.txt      the ASCII render of the last run

./sigil status | grammar | build | run | present | explain F###
```

`build` compiles aspect-locked units into scene IR (C-style faults, terse).
`run` executes and **always renders the artifact back as a 160×60 ASCII view**
plus a census — the agent's primary feedback. `present` submits for hidden
semantic verification: **3 presents and 40 toolchain invocations per level;
exhausting either ends the entire run.** Optional image mode (`sigil.toml
[view] mode="image"`) also writes `out/render.png` for multimodal harnesses.

## Scoring

The build log (with full embedded sources) is replayed host-side against the
true hidden goals — sandbox tampering cannot change the score, and the
reference solutions never enter the runtime.

- reward `progress` — levels cleared / gauntlet length
- metrics — `levels_completed`, `toolchain_calls`, `failed_builds`,
  `runtime_traps`, `presents_used`, `mean_regret_stmts` (final program
  statements beyond the hidden reference program), `run_terminated`

## Config

```
--taskset.start-level 1     # 1-based curriculum index
--taskset.num-levels 10     # gauntlet length (200 = full curriculum)
```

## Run

```bash
prime eval validate diagrambench-v1                      # gold replay
prime eval run diagrambench-v1 --taskset.num-levels 10 \
  --harness.id codex --harness.runtime.type prime -m <model>
```
