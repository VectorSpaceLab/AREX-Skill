# Installation and runtime boundaries

`paperai` 2.6.0 declares Python `>=3.10` and installs the runtime dependencies
needed for SQLite access, YAML parsing, text processing, txtai embeddings/API,
static vector training, and PDF annotation support:

```bash
python -m pip install "paperai==2.6.0"
```

Use a private virtual environment or Conda/venv prefix for inspection and
application work. The package exposes the console entry point
`paperai = paperai.shell:main`; module entry points include
`python -m paperai.index`, `python -m paperai.query`,
`python -m paperai.export`, `python -m paperai.vectors`, and
`python -m paperai.report`.

The distribution does not declare a dedicated CUDA/ROCm/MPS extra. txtai and
its selected model/backend may install or require framework-specific packages,
model weights, device libraries, or network access. Treat those as a separate
model/runtime decision. The core paperai capability is usable on CPU when the
chosen txtai model supports it, but importability alone does not validate a
model or accelerator.

The `txtai[api]` dependency supplies the API stack used by `paperai.api.API`.
`txtmarker` and PDF-related dependencies support the optional `ant` annotation
renderer. Streamlit, pandas, and HTML-cleaning packages used by the example UI
are not declared as paperai core requirements; install them only for that
optional application.

## Minimal smoke check

```bash
python -c "import paperai, paperai.index, paperai.query, paperai.report.execute; print('paperai imports OK')"
python -m pip check
```

Then use the bundled corpus/config validators before any model download. The
validators do not import txtai, mutate the corpus, or fetch remote weights.
