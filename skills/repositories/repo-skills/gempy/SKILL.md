---
name: gempy
description: "Use GemPy 3.x for CPU-first 3-D implicit geological modeling,
  structural data preparation, grid evaluation, visualization, persistence, and
  optional integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: EUPL 1.2
---

# GemPy operating skill

Use this skill when a Researcher needs to build, compute, inspect, serialize, or
troubleshoot a GemPy 3.x geological model. It is distilled from a versioned
public package surface and is self-contained: workflows use caller-owned arrays,
tables, and paths rather than checkout-relative examples or downloaded data.

## Route the request

Choose the narrowest route before writing code:

- **Create, map, validate, compute, faults, or unconformities:**
  [`modeling`](sub-skills/modeling/SKILL.md)
- **Surface points, orientations, CSV input, IDs, elements, groups, or table
  mutation:** [`data-and-structure`](sub-skills/data-and-structure/SKILL.md)
- **Dense/custom/section/centered/topography grids, coordinate queries, or
  plots:** [`grids-and-visualization`](sub-skills/grids-and-visualization/SKILL.md)
- **`.gempy`/JSON persistence, mesh extraction, gravity, topology, properties,
  Subsurface, or legacy adapters:**
  [`serialization-and-advanced`](sub-skills/serialization-and-advanced/SKILL.md)
- **Installation, imports, package drift, backend/device, optional packages,
  or headless rendering:**
  [`environment-and-troubleshooting`](sub-skills/environment-and-troubleshooting/SKILL.md)

For a multi-stage request, follow the usual order:
**environment → data/structure → modeling → grid/evaluation → persistence or
visualization**. Return to the owning route when a failure crosses a boundary;
do not mask a data error by changing the backend or installing unrelated
optional packages.

## Install and verify the public package

Use a fresh Python 3.10+ environment and keep pip attached to that interpreter:

```bash
python -m pip install gempy
python -m pip check
python -c "import gempy, gempy_engine; print(gempy.__version__)"
```

Add the base extra only for pandas/table readers or GemPy Viewer workflows:

```bash
python -m pip install "gempy[base]"
```

Install optional scientific, plugin, Subsurface, PyVista, or PyTorch packages
only for the corresponding route. The environment route's checker is read-only:
`python sub-skills/environment-and-troubleshooting/scripts/check_environment.py
--json`.

## Core operating rules

1. Prefer `import gempy as gp` and public `gp.data`/`gp.*` APIs. Verify the
   installed GemPy, `gempy_engine`, and (if used) `gempy_viewer` release line
   before relying on a changed signature.
2. Start with a small dense grid and NumPy:
   `GemPyEngineConfig(backend=gp.data.AvailableBackends.numpy, use_gpu=False)`.
   PyTorch/CUDA, PyKeOps, viewer/PyVista, SciPy/scikit-image, GSTools,
   `gempy_plugins`, Subsurface, and `gempy_legacy` are optional boundaries,
   not proof obligations for the core route.
3. Build or load a `StructuralFrame`, add caller-owned input data, map elements
   to final structural groups, then call `model.validate()` before
   `gp.compute_model()`. Preserve `ModelValidationError.reason`, `.field`, and
   `.context` when repair is needed.
4. Grid setters activate flags without necessarily clearing earlier components;
   inspect `model.grid.active_grids`, use `reset=True` intentionally, and
   recompute after grid changes. `compute_model_at` is stateful and leaves a
   custom grid active.
5. Keep `.gempy` archives and JSON files in caller-owned temporary or output
   paths. Load and compare structure/input counts before trusting a round trip;
   recompute restored models when solutions are needed.
6. Do not fetch network examples, open interactive viewers in headless jobs, or
   claim an optional backend works from a CPU import. See
   [`references/troubleshooting.md`](references/troubleshooting.md) for the
   cross-cutting decision sequence.

## Bundled diagnostics

The sub-skills contain deterministic helpers that do not install packages,
fetch data, or read the source checkout:

- `sub-skills/environment-and-troubleshooting/scripts/check_environment.py`
  checks Python, core imports, optional modules, and selected backends.
- `sub-skills/modeling/scripts/tiny_model_smoke.py` builds and computes a tiny
  in-memory CPU model.
- `sub-skills/grids-and-visualization/scripts/grid_smoke.py` checks dense,
  custom, active-grid, and section semantics without a viewer.
- `sub-skills/data-and-structure/scripts/inspect_tables.py` reports caller-owned
  CSV table shape, names, IDs, and finite-value counts without modifying files.
- `sub-skills/serialization-and-advanced/scripts/json_roundtrip_smoke.py`
  checks tiny `.gempy` and JSON round trips in temporary output.

Run these from the generated skill directory or by passing their absolute path;
read the owning route first so a smoke result is not mistaken for geological
correctness.

## Freshness and limits

The package facts are tied to the commit and evidence listed in
[`references/repo-provenance.md`](references/repo-provenance.md). Optional
plugins, GPU/autodiff, external data readers, and interactive 3-D rendering are
explicitly bounded; if a request depends on one, verify that dependency and
runtime separately. The review artifacts under `skills/tests/gempy/` are
construction and verification records, not runtime dependencies.
