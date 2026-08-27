# Cross-cutting troubleshooting

This file covers install, import, and package-level issues that can affect both tabular and forecasting workflows.

## Missing `automl_common` submodule

**Symptoms**

- `ModuleNotFoundError: No module named 'autoPyTorch.automl_common.common'`
- core task imports fail immediately from a source checkout

**Likely cause**

The repository uses the `autoPyTorch/automl_common` Git submodule, and it has not been initialized.

**Recovery**

- If you are working from a source checkout, initialize the submodule before importing the package.
- If you are using a released wheel, install the package normally from PyPI instead of a partial checkout.

## Forecasting extras missing

**Symptoms**

- `ImportError` when importing `TimeSeriesForecastingTask`
- `ModuleNotFoundError` for `gluonts`, `sktime`, or `pytorch_forecasting`

**Likely cause**

The forecasting APIs require the forecasting extra.

**Recovery**

- Install `autoPyTorch[forecasting]`.
- Re-run the import check from a clean Python session.

## Version or wheel mismatches

**Symptoms**

- build failures for `ConfigSpace`, `pyrfr`, or other compiled packages
- `ImportError` or ABI errors after installing a newer `scikit-learn` or unrelated torch stack

**Likely cause**

Auto-PyTorch 0.2.1 targets an older scientific Python stack than many modern ML projects.

**Recovery**

- Use a supported Python version from the repo docs and CI history.
- Keep `scikit-learn` in the repository-supported range.
- Prefer wheels over source builds when possible.
- If a source build is required, make sure the host has the expected compiler and SWIG support.

## Example data downloads fail

**Symptoms**

- OpenML fetches fail in examples or tests
- example notebooks or scripts hang while downloading data

**Likely cause**

Many examples and some tests use network-backed sample data.

**Recovery**

- Use cached data or a synthetic fixture when you only need a smoke test.
- Treat the original examples as workflow references, not as guaranteed offline scripts.

## Visualization feels broken

**Symptoms**

- plotting helpers fail in headless environments
- `plot_perf_over_time()` runs but no figure appears

**Likely cause**

The plot backend or display environment is missing.

**Recovery**

- Use a non-interactive matplotlib backend.
- Save the figure to a file instead of showing it interactively.

## CPU vs CUDA confusion

**Symptoms**

- torch reports CUDA support but the workflows still look CPU-oriented
- a GPU host exists, but the selected Auto-PyTorch task does not require it

**Likely cause**

The core Auto-PyTorch tabular and forecasting workflows are not GPU-only.

**Recovery**

- Do not treat a CUDA-enabled torch wheel as proof that a workflow requires GPU execution.
- Follow the workflow-specific route and the selected backend plan.

## Where to look next

- `sub-skills/tabular-automl/references/troubleshooting.md`
- `sub-skills/forecasting/references/troubleshooting.md`
