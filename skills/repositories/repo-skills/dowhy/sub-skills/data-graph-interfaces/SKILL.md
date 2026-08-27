---
name: data-graph-interfaces
description: "Operate DoWhy graph, pandas do-accessor, sampler, dataset,
  transformer, plotting, and time-series interfaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data and Graph Interfaces

Use this sub-skill for the shared interface layer that sits between raw data,
graphs, samplers, datasets, plotting, and time-lag helpers.

## Route here

- Build or inspect causal graphs from NetworkX, DOT, GML, or DAGitty text.
- Align graph nodes, data columns, and lagged columns before downstream tasks.
- Use the pandas `.causal.do` accessor or a `DoSampler`.
- Choose variable types, sampler methods, or stateful reuse.
- Create synthetic datasets or reduce features before graph-based workflows.
- Prepare lagged or temporal graph abstractions.

## Route away

- If the user wants classic `CausalModel` effect estimation, identification,
  `do`, or refutation, route to [../effect-estimation/SKILL.md](../effect-estimation/SKILL.md).
- If the user wants `dowhy.gcm` sampling, interventions, attribution, or
  validation, route to [../graphical-causal-models/SKILL.md](../graphical-causal-models/SKILL.md).
- If the user wants to learn a graph from data, treat
  `CausalModel.learn_graph()` and `dowhy.graph_learners` as deprecated. Hand
  discovery off to an external causal-discovery library, then return here only
  for import and alignment.

## Read first

- [references/data-graph-interfaces.md](references/data-graph-interfaces.md)
- [references/pandas-do-sampler.md](references/pandas-do-sampler.md)
- [references/time-series.md](references/time-series.md)
- [references/troubleshooting.md](references/troubleshooting.md)

## Task selector

1. Need to normalize graph input? Use `build_graph_from_str`, `CausalGraph`, or
   `build_graph`.
2. Need interventional samples from a pandas frame? Use `df.causal.do` and the
   do-sampler references.
3. Need a built-in synthetic dataset or a simple feature reducer? Use the
   dataset and transformer references.
4. Need lagged graph or lagged column handling? Use the time-series helpers.
5. Need graph plotting? Use the plotting helpers with the optional backend note
   in troubleshooting.

## Operating protocol

- Confirm graph nodes and DataFrame columns map cleanly before handing off to a
  downstream causal task.
- Prefer NetworkX `DiGraph` as the in-memory representation; accept DOT, GML,
  or DAGitty only as normalized inputs.
- For pandas do-sampling, remember that `x` may be a string, list, or dict.
  String/list keeps the original treatment values; dict sets intervention
  values.
- Treat `stateful=True` as a cache for repeated calls on the same accessor, and
  call `reset()` when you want a clean sampler state.
- If the user now needs effect estimation, refutation, or GCM queries, stop
  here and hand off to the sibling skill.

## Minimal smoke check

Run the bundled smoke script to exercise graph parsing, pandas do-sampling,
datasets, transformers, and temporal helpers:

```bash
python scripts/smoke_graph_and_do.py --help
```

Use the script as a safe starting point for quick validation or for adapting
these interface patterns into another project.
