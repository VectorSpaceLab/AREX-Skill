---
name: hypertools
description: "Plot, load, analyze, text, and forecast with HyperTools."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# HyperTools

Use this skill when a task involves the HyperTools package, its public APIs,
or a workflow that combines plotting, loading, stage pipelines, text
conversion, forecasting, or imputation.

## Start here

- Read `references/repo-provenance.md` to confirm the generated skill matches
  the current package state.
- Read `references/api-overview.md` for the exported surface, common return
  shapes, and shared conventions.
- Read `references/troubleshooting.md` when imports, extras, file formats, or
  backend selection fail.
- Run `scripts/check-install.py` for a tiny import/config/plot/save-load smoke.
- Run `scripts/check-backends.py` when you need optional plotly, gensim,
  density3d, xlsx, or LSL coverage.

## Install

```bash
pip install hypertools
```

Add only the extra that matches the task:

- `hypertools[interactive]` for plotly rendering and image export
- `hypertools[io]` for Excel support
- `hypertools[gensim]` for gensim text models
- `hypertools[lsl]` for Lab Streaming Layer streams
- `hypertools[density3d]` for 3-D density iso-surfaces
- `hypertools[predict]` for the Laplace forecaster
- `hypertools[predict-hf]` for Chronos forecasting
- `hypertools[kaggle]` for Kaggle datasets
- `hypertools[text]` for Hugging Face text embeddings
- `hypertools[torch]` for torch-backed autoencoders

## Route map

### `sub-skills/visualization/SKILL.md`
Use for `hyp.plot(...)`, backend selection, animation, styling, `save_path`,
streaming plots, `surface`/`density`, `MultiIndex` rendering, and forecast
overlays.

### `sub-skills/io/SKILL.md`
Use for `hyp.load`, `hyp.save`, source resolution, trust decisions, built-in
datasets, and `hyp.io.lsl_stream(...)`.

### `sub-skills/pipeline/SKILL.md`
Use for `manip`, `normalize`, `reduce`, `align`, `cluster`, `apply_model`,
`Pipeline`, stage ordering, model-spec grammar, and fitted-model reuse.

### `sub-skills/text/SKILL.md`
Use for `text2mat`, text-aware `hyp.plot(...)`, `vectorizer=`, `semantic=`,
`corpus=`, sklearn text models, gensim wrappers, and Hugging Face fallback
behavior.

### `sub-skills/forecasting/SKILL.md`
Use for `hyp.predict`, `hyp.impute`, reusable forecasters/imputers, horizon
rules, and forecast-overlay model selection.

## Shared behavior

- HyperTools 1.0 uses a unified public surface: `plot`, `analyze`, `reduce`,
  `align`, `normalize`, `describe`, `cluster`, `manip`, `predict`, `impute`,
  `load`, `save`, `apply_model`, `Pipeline`, `set_interactive_backend`,
  `HyperAnimation`, `io`, and `supported_models`.
- The canonical analysis order is `manip -> normalize -> reduce -> align ->
  cluster`.
- `plot` returns a matplotlib `Figure`, a plotly `Figure`, or a
  `HyperAnimation` depending on backend and animation settings.
- `analyze(..., cluster=...)` returns transformed data; recover labels from the
  fitted cluster step when `return_model=True`.
- `load` returns raw data or a stream object, while `save` writes by filename
  extension.
- If a request spans routing boundaries, start with the owning sub-skill and
  hand off the adjacent concern there instead of widening this root router.

## Quick smoke habits

- Prefer `show=False` for batch checks.
- Prefer tiny synthetic arrays, DataFrames, or corpora over repo examples when
  you only need to confirm package behavior.
- Keep backend-specific checks local to the matching sub-skill or the bundled
  smoke scripts.
