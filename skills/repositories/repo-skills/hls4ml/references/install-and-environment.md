# Install and Environment Guide

## Purpose

Read this when you need to install hls4ml or decide which optional extras to add for a particular workflow.

## Base install

- `pip install hls4ml`

This gives the core package and is enough for import checks, backend registry inspection, and many source-backed operations.

## Common extras by workflow

- `hls4ml[testing]` — PyTorch, ONNX, QONNX, pytest, and report-helper dependencies used by many frontend and backend smoke checks.
- `hls4ml[testing-keras2]` — TensorFlow/Keras 2, QKeras, and HGQ support for Keras v2 workflows.
- `hls4ml[profiling]` — profiling plots and dataframe/plotting dependencies.
- `hls4ml[da]` — distributed-arithmetic support package.
- `hls4ml[snn]` — snntorch support for the PyTorch SNN route.
- `hls4ml[sr]` — symbolic regression utilities.
- `hls4ml[optimization]` — model optimization / pruning / weight-sharing extras; see the compatibility note below.

## When you need a separate environment

- Keras v3, QKeras-v3, HGQ2, PQuantML, and sparsepixels are a separate Keras 3 family. Use a dedicated environment for those paths instead of mixing them with the Keras 2 family.
- The `optimization` extra pins `ortools==9.4.1874`. In the inspection environment, that pin did not resolve cleanly on Python 3.11. Use Python 3.10 or a compatible dependency set if you need runtime verification of the model-optimization APIs.
- If TensorFlow/Keras, ONNX, and version-pinned low-level numeric packages conflict, keep the package family you are actively using and split the others into a separate environment.

## Minimal import check

```bash
python -c "import hls4ml; print(hls4ml.__version__)"
```

For a richer local smoke check, use `scripts/check_install.py`.

## What not to do

- Do not install vendor HLS synthesis tools through pip.
- Do not assume `hls4ml` itself provides GPU workflows; GPU availability is optional and not required for the core package.
- Do not mix the Keras 2 and Keras 3 families in the same Python environment.
