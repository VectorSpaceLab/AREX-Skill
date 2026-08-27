# HyperTools Troubleshooting

Use this page for cross-cutting install, import, file-format, and backend
issues. Route workflow-specific issues to the matching sub-skill.

## Import or install fails

### Symptom
`import hypertools` raises `ModuleNotFoundError` or a base dependency is
missing.

### Fix
- Install the package in an isolated environment: `pip install hypertools`
- Run `python -m pip check`
- Confirm the import comes from the intended environment before debugging a
  workflow problem

### Notes
The package requires Python `>=3.10` and depends on the scientific stack that
ships with the base install.

## Optional extras are missing

### Symptom
A workflow-specific helper complains about `plotly`, `gensim`, `pylsl`,
`openpyxl`, `scikit-image`, `torch`, `kagglehub`, `pydata-wrangler[hf]`, or
`skaters`.

### Fix
Install only the extra needed by the workflow:

```bash
pip install "hypertools[interactive]"
pip install "hypertools[gensim]"
pip install "hypertools[lsl]"
pip install "hypertools[io]"
pip install "hypertools[density3d]"
pip install "hypertools[torch]"
pip install "hypertools[kaggle]"
pip install "hypertools[text]"
pip install "hypertools[predict]"
pip install "hypertools[predict-hf]"
```

## Plotting backend confusion

### Symptom
`backend='plotly'` or `set_interactive_backend('plotly')` falls back, or a
matplotlib interactive plot behaves unexpectedly.

### Fix
- Use `show=False` for smoke tests and batch runs
- Prefer `backend='auto'` unless you need an explicit renderer
- Keep `plotly` issues in `sub-skills/visualization/`

## File format and source loading issues

### Symptom
`hyp.load` or `hyp.save` rejects a filename, a remote source, or a legacy file.

### Fix
- Use a supported extension: `.csv`, `.tsv`, `.txt`, `.npy`, `.npz`, `.json`,
  `.parquet`, `.mat`, `.xlsx`, or a pickle-style extension
- For remote pickle-backed data, require an explicit trust decision
- For `.xlsx`, install `hypertools[io]` or `openpyxl`
- For built-in datasets and source precedence, use `sub-skills/io/`

## Plot export issues

### Symptom
PNG, HTML, or movie export fails, or the save path is invalid.

### Fix
- Use `hyp.plot(..., save_path=...)` for figure export
- Create parent directories before saving
- For matplotlib video containers, install `ffmpeg` on the host
- For plotly static export, install the `interactive` extra and any required
  browser/kaleido support
- Keep styling and export questions in `sub-skills/visualization/`

## Workflow errors that need a sibling sub-skill

- `manip`, `normalize`, `reduce`, `align`, `cluster`, `apply_model`,
  `Pipeline`, `ndims`, or reuse errors -> `sub-skills/pipeline/`
- `text2mat`, `vectorizer=`, `semantic=`, `corpus=`, or Hugging Face fallback
  -> `sub-skills/text/`
- `predict`, `impute`, horizon validation, or forecast overlay model choice ->
  `sub-skills/forecasting/`
- LSL and load/save source resolution -> `sub-skills/io/`
- Plot styling, animation, density, surfaces, streaming, or renderer choice ->
  `sub-skills/visualization/`
