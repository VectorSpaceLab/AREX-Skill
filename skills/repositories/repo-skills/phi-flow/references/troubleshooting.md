# PhiFlow Troubleshooting

## Purpose

Use this for cross-cutting PhiFlow failures that are not specific to one
workflow sub-skill yet. For workflow-specific problems, follow the nearest
sub-skill reference first.

## Install and import failures

**Symptom:** `ModuleNotFoundError: phiml` or `ImportError: No module named phi`.

- Install the repository editable from the checkout root with `python -m pip
  install -e .`, or install the published `phiflow` package.
- Make sure the environment is the one you are inspecting, not a different
  Python on `PATH`.
- Re-run the bundled `scripts/check_install.py` smoke helper after the install.

**Symptom:** `python -m pip check` reports a broken requirement set.

- Reinstall the package set in a fresh environment if the current environment is
  already in use.
- Check that `phiflow`, `phiml`, `matplotlib`, and any selected backend wheels
  are compatible with the Python version in the environment.

## Backend and minimal config issues

**Symptom:** `phi.verify()` prints that Dash or Plotly is missing.

- Install `dash` and `plotly` for the web UI workflow.
- If you only need notebook or Matplotlib plots, the fallback is usually fine,
  but do not claim web-UI readiness without Dash and Plotly.

**Symptom:** `phi.detect_backends()` does not list `torch`, `jax`, or
`tensorflow`.

- Install the backend wheel you actually want to use.
- A CPU import alone does not prove GPU readiness.
- Only claim a backend after the package and the hardware path are both
  available.

## Stale docs and stale API names

**Symptom:** older docs mention `view()`.

- This version exposes `show()` and `plot()` from `phi.vis`, not a public
  `view()` launcher.
- Use the visualization sub-skill for plotting and UI workflows.

**Symptom:** older examples use `Box[0:1, 0:1]` or `Domain(...)` as a normal
pattern.

- Prefer `Box['x,y', 0:1, 0:1]` or keyword constructors like `Box(x=1, y=1)`.
- `Domain` is legacy compatibility only.
- Use direct grid constructors with `extrapolation=` / `boundary=` instead.

## When to stop

Stop and switch sub-skills if the issue is really about:

- scene round-trips or field data formats -> core-data-and-geometry
- advection / diffusion / fluids / waves / SPH -> physics-and-simulation
- gradients, Jacobians, or inverse problems -> optimization-and-learning
- plotting, controls, or scalar logs -> visualization-and-ui
