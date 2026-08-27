---
name: visualization
description: "Build and troubleshoot Mesa visualizations with SolaraViz,
  SpaceRenderer, component builders, portrayal styles, user params, and headless
  stack checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Visualization

Use this sub-skill when the task is to build, adapt, or debug a Mesa browser/notebook visualization rather than to change the model, space, or metric definitions.

## Use this for

- `SolaraViz` / `JupyterViz` dashboards and component layout.
- `SpaceRenderer` with Matplotlib or Altair backends.
- `make_space_component` and `make_plot_component` component builders.
- `AgentPortrayalStyle`, `PropertyLayerStyle`, dynamic portrayals, and property-layer overlays.
- `model_params` widgets, reset-time model construction, and the optional command console.
- Safe headless import/signature checks with the bundled script.

## Route elsewhere

- Model constructors, activation, `step()`, `run_for()`, and simulation semantics: [../model-core/SKILL.md](../model-core/SKILL.md).
- Grid/network/continuous space topology and property-layer creation: [../spaces/SKILL.md](../spaces/SKILL.md).
- `DataCollector` reporter definitions and experiment metric design: [../analysis-experiments/SKILL.md](../analysis-experiments/SKILL.md).

## Start here

1. Check public signatures, style fields, backend choices, and the `model_params` reset contract in [references/api-reference.md](references/api-reference.md).
2. Use the authoring recipes in [references/workflows.md](references/workflows.md) for dashboards, dynamic portrayals, plots, property layers, custom components, and headless checks.
3. Diagnose import, browser, constructor, portrayal, plot, and backend failures with [references/troubleshooting.md](references/troubleshooting.md).
4. Run [scripts/check_visualization_stack.py](scripts/check_visualization_stack.py) when you need a no-server, no-browser stack probe.

## High-signal rules

- `SolaraViz` re-creates models with `**model_parameters.value`; every key in `model_params` must match a keyword accepted by the model constructor, a scenario field handled by the model, or `**kwargs`.
- Prefer `SpaceRenderer` for layered space structure, agents, property layers, and backend-specific styling. Use `make_space_component` for a lighter built-in space component.
- Match `post_process` to the backend: Matplotlib receives an `Axes`; Altair receives a `Chart`.
- Browser or Playwright end-to-end checks are optional. A baseline visualization readiness check should start with import/signature validation and safe component construction patterns.
