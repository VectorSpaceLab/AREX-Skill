---
name: mesa
description: "Use Mesa for agent-based simulation models, spatial ABM
  environments, experiment data collection, scenarios, and Solara visualization
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Mesa

Use this repo skill when a task involves **Mesa**, the Python agent-based modeling framework: building ABM models, managing agents, adding spaces, collecting outputs, running scenarios, or creating browser/notebook visualizations.

## Install and import

Mesa requires Python 3.12 or newer in this snapshot.

```bash
python -m pip install -U mesa
# For Mesa 4 pre-releases when a task depends on APIs from this skill:
python -m pip install -U --pre mesa
# Recommended optional stacks:
python -m pip install -U "mesa[network]"  # Network spaces
python -m pip install -U "mesa[viz]"      # Solara/matplotlib/altair visualization
python -m pip install -U "mesa[rec]"      # network + viz recommended extras
```

Minimal import check:

```python
import mesa
from mesa import Agent, DataCollector, Model
from mesa.discrete_space import OrthogonalMooreGrid
```

Run [scripts/check_mesa_install.py](scripts/check_mesa_install.py) for a safe JSON probe of the installed package and optional extras.

## Route by task

| Task intent | Read |
| --- | --- |
| Define `Model` and `Agent` classes, create agents, activate `AgentSet`s, seed RNGs, schedule events, run time, remove agents | [model-core](sub-skills/model-core/SKILL.md) |
| Choose grids/cells/network/Voronoi/continuous spaces, move cell agents, use property layers, debug capacity or coordinates | [spaces](sub-skills/spaces/SKILL.md) |
| Collect model/agent/table outputs, create DataFrames, run scenarios, use experimental recorders/actions/states/signals | [analysis-experiments](sub-skills/analysis-experiments/SKILL.md) |
| Build or debug `SolaraViz`, `SpaceRenderer`, component builders, portrayal styles, plots, user parameters, visualization extras | [visualization](sub-skills/visualization/SKILL.md) |

## High-signal Mesa rules

- In Mesa 4, `Agent.__init__(model)` automatically registers the agent and assigns `unique_id`. Do not reassign or manually mutate `model.agents`.
- `Model(rng=...)` creates both `model.rng` and `model.random`; pass `rng` for reproducibility unless a `Scenario` instance already owns the RNG.
- `Model.step()` is scheduled by default every 1.0 time units; use `run_for()` or `run_until()` to process the event queue.
- Prefer `model.agents.do(...)`, `shuffle_do(...)`, `map(...)`, `select(...)`, `groupby(...)`, and `agg(...)` over custom scheduler objects.
- For new spatial models, use `mesa.discrete_space` or `mesa.experimental.continuous_space`, not legacy `mesa.space` APIs.
- `DataCollector` supports model, agent, agent-type, and table outputs; avoid lambdas when the model must be pickle-safe.
- `SolaraViz` re-creates models from `model_params`; model constructors must accept keyword arguments matching those parameter keys.

## Optional dependency choices

- Core modeling, data collection, grids, Voronoi, and continuous spaces: base `mesa` install.
- Network examples or `Network` default layouts: install `mesa[network]` or pass your own graph/layout stack.
- Browser/notebook visualization: install `mesa[viz]` or `mesa[rec]`.
- Example-library and verification-style runs: `mesa[examples]` includes recommended extras and pytest.
- Browser end-to-end checks need additional frontend/browser tooling and are not required for ordinary modeling tasks.

## References and checks

- [references/repo-provenance.md](references/repo-provenance.md) records the source snapshot used to create this skill; read it before deciding whether to refresh the skill for a different checkout or Mesa version.
- [references/examples-index.md](references/examples-index.md) maps classic Mesa example patterns to the owning sub-skills.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting install, version, optional-extra, and workflow-selection issues.
- Each sub-skill links its own API reference, workflows, troubleshooting guide, and smoke scripts.

## Avoid this skill when

- The task is only generic Python, pandas, NumPy, NetworkX, Matplotlib, Altair, or Solara usage without Mesa model objects or Mesa visualization components.
- The task asks for a non-Mesa ABM framework such as NetLogo, Repast, MASON, Agents.jl, or a custom simulator.
- The task is benchmark-scale performance tuning or browser automation infrastructure; this skill records those as long-tail or optional areas, not primary guidance.
