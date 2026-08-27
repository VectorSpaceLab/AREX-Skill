# Cross-Cutting Troubleshooting

## Purpose

Use this for issues that affect more than one hls4ml sub-skill: import failures, optional dependency conflicts, backend prerequisite problems, and CLI confusion.

## Common failures and next steps

### `ImportError` or missing core dependency

**Symptoms**
- `No module named 'quantizers'`
- `No module named 'pydigitalwavetools'`
- `Failed to import hls4ml`

**Likely cause**
- The base package or its dependencies were not installed.

**Next step**
- Install the base package first: `pip install hls4ml`
- Then add the workflow-specific extras from `references/install-and-environment.md`.
- Re-run `scripts/check_install.py`.

### Keras 2 vs Keras 3 conflicts

**Symptoms**
- TensorFlow/Keras import errors after installing Keras 3 extras
- `qkeras` or `tensorflow-model-optimization` compatibility problems

**Likely cause**
- Keras 2 and Keras 3 families were mixed in one environment.

**Next step**
- Keep Keras 2 workflows in a TensorFlow 2.14 environment.
- Use a separate Keras 3 environment for `keras-v3`, `qkeras-v3`, `hgq2`, `pquant-ml`, or `sparsepixels`.

### ONNX import mismatch with TensorFlow numerics

**Symptoms**
- ONNX import fails with `ml_dtypes` attribute errors
- A newer ONNX wheel pulls numeric types that conflict with TensorFlow 2.14 pins

**Likely cause**
- The installed ONNX wheel is too new for the TensorFlow/Keras 2 environment.

**Next step**
- Pin ONNX to a compatible version such as `onnx==1.16.1` in the Keras 2 inspection env.
- If you need a different ONNX stack, split it into a separate environment.

### Optimization extra resolver failure

**Symptoms**
- `ortools==9.4.1874` cannot be resolved for Python 3.11
- `pip install hls4ml[optimization]` fails during dependency resolution

**Likely cause**
- The pinned ortools version is not available for the active Python/version combination on the configured index.

**Next step**
- Use Python 3.10 or another compatible environment if model-optimization runtime verification is required.
- If you only need the docs, keep the optimization workflow as source-documented.

### Missing backend prerequisite tools

**Symptoms**
- `Vivado HLS installation not found`
- `Quartus installation not found`
- `shls` command not found
- `catapult` or `vitis-run` missing
- SymbolicExpression config asks for Vivado/Vitis HLS include files

**Likely cause**
- Vendor toolchain paths are missing from PATH or the include/library paths have not been configured.

**Next step**
- Confirm the backend in `references/backend-matrix.md`.
- Install or source the required vendor environment.
- Use `scripts/inspect_backends.py` to see which default config fields are available and which prerequisite errors are expected.

### Deprecated CLI confusion

**Symptoms**
- `hls4ml config/convert/build/report` looks unfamiliar or is missing from PATH
- Legacy CLI usage text differs across environments

**Likely cause**
- The CLI is deprecated and the Python API is the preferred path.

**Next step**
- Prefer the Python API from the relevant sub-skill.
- Use `scripts/check_cli_help.py` only to confirm the legacy interface when needed.

### Unsupported operator or layer

**Symptoms**
- conversion fails with an unsupported layer/operator message
- the generated graph is missing a frontend-specific quantized or spiking layer

**Likely cause**
- The model uses an operator outside the supported surface or needs a separate frontend family.

**Next step**
- Check the correct frontend reference in the `frontends` sub-skill.
- If the operator is custom, move to `extensions`.
- If the model family is Keras 3 or another separate dependency set, split into the matching environment.

## Next probes

- `scripts/check_install.py` for a quick environment snapshot.
- The relevant sub-skill helper script for a safe frontend/backend/analysis probe.
