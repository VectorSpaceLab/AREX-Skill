---
name: analysis-experiments
description: "Collect Mesa experiment data, run scenario sweeps, and use
  experimental actions, states, signals, and meta-agent analysis helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Analysis Experiments

Use this sub-skill when a Mesa task is about **experiment outputs, scenario orchestration, or experimental analysis helpers** rather than basic model structure or visualization.

## Use for

- `DataCollector` reporters, model / agent / agent-type DataFrames, and manual tables.
- Experimental `mesa.experimental.data_collection` datasets, registries, and recorders.
- Experimental `Scenario`, `RunConfiguration`, `run_scenarios`, stores, statuses, and failure diagnostics.
- Experimental timed `Action` lifecycles, continuous states, thresholds, reactive signals, and batching.
- Experimental `MetaAgent` grouping utilities for higher-order agent analysis.

## Start here

- [API reference](references/api-reference.md) for signatures, import paths, return shapes, and stability notes.
- [Workflows](references/workflows.md) for copyable collection, recorder, scenario, signal/state/action, and meta-agent recipes.
- [Troubleshooting](references/troubleshooting.md) for reporter validation, recorder setup, scenario failure origins, pickling, and experimental API pitfalls.
- [DataCollector smoke script](scripts/datacollector_smoke.py) for a safe installed-package check that emits JSON summaries.
- [Scenario smoke script](scripts/scenario_smoke.py) for a safe installed-package check of `Scenario`, `RunConfiguration`, `run_scenarios`, and failure recording.

## Route elsewhere

- Core `Model`, `Agent`, `AgentSet`, activation, RNG, and event scheduling basics: [model-core](../model-core/SKILL.md)
- Spatial placement, movement, grids, networks, cells, or continuous-space geometry: [spaces](../spaces/SKILL.md)
- Solara dashboards, browser visualization, plotting widgets, charts, or rendering: [visualization](../visualization/SKILL.md)

All APIs under `mesa.experimental` are experimental and may change between Mesa releases. Treat this sub-skill as the self-contained operating reference; no external repository files are required at runtime.
