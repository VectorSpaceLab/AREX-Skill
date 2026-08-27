# GemPy provenance

`schema: disco.repo-provenance.v1`

This operating skill was distilled from the public GemPy checkout at:

- **Commit:** `6ebbd2e9499e599929e40e7e97b31364770ea605`
- **Branch:** `main`
- **Source dirty state at inspection:** clean before skill artifacts were written
- **Package:** `gempy`
- **Observed distribution metadata version:** `3.0.1.dev1+g6ebbd2e94.d20260820`
- **Observed imported `gempy.__version__`:** `2024.2.0.3.dev0+gf344a731.d20240626`
- **Observed companion versions:** `gempy_engine 2026.1.0a1`, `gempy_viewer 2026.0.5`
- **Version consistency note:** the editable inspection checkout exposed a
  metadata/import version mismatch. Treat the distribution metadata and
  imported module version as separate facts; run the bundled checker and align
  the installed package/source before making a release-specific claim.
- **Import root:** `gempy`
- **Inspection scope:** public `gempy/`, `gempy/API/`, `gempy/core/data/`,
  `gempy/modules/`, public docs, examples, tests, requirements, and safe
  workflow evidence
- **Verification backend:** CPU/NumPy core path; base/viewer imports were
  inspected. PyTorch/CUDA, PyKeOps, GSTools, Subsurface, plugins, and legacy
  integrations were not required and remain optional/unverified.

## Relative evidence map

- `README.md`, `setup.py`, `setup.cfg`, `requirements/`: package purpose,
  installation variants, and dependency boundaries.
- `gempy/API/`: public construction, compute, grid, fault, input mutation,
  mapping, persistence, and compatibility entry points.
- `gempy/core/data/`: frames, groups, elements, tables, grids, enums, options,
  and semantic validation.
- `gempy/modules/`: JSON I/O, archive persistence, mesh extraction, topography,
  and geophysics helpers.
- `gempy/VALIDATION_SPEC.md`: validation precedence and structured error fields.
- `docs/source/`: public installation and API intent.
- `examples/examples/geometries/`, `examples/tutorials/`,
  `examples/integrations/`: workflow intent and optional integration evidence;
  distilled recipes use no source-relative paths or network data.
- `test/test_api/`, `test/test_modules/`: behavioral and edge-case evidence;
  native cases are verification inputs, not runtime dependencies.

## Refresh signal

Refresh this skill when GemPy's public signatures, structural-frame hierarchy,
validation reasons, engine configuration, archive/JSON formats, or viewer/grid
side effects change. Compare the installed GemPy, engine, and viewer versions
and rerun the relevant bundled smoke helpers before relying on a new behavior.
