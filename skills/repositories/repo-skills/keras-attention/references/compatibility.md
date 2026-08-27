# Compatibility and environment notes

## Package identity

- Public package/distribution: `attention`.
- Import module: `attention`.
- Public class: `Attention`.
- Version in the inspected source metadata: `5.0.0`.
- Runtime dependencies declared by the package: `numpy>=1.18.1` and
  `tensorflow>=2.1`.
- No package extras and no console entry points are declared.

## TensorFlow and Keras versions

The repository README says the project was tested with TensorFlow 2.8 through
2.14. The repo's tox configuration also includes TensorFlow 2.15. A focused
inspection smoke for this skill passed with TensorFlow 2.15.1, Keras 2.15.0,
NumPy 1.26.4, and Python 3.11.

Practical guidance:

- Prefer a TensorFlow 2.x stack close to the documented/tested range when a
  user's environment is flexible.
- If TensorFlow/Keras 2.16+ or standalone Keras 3 is already installed, run the
  bundled smoke script before relying on serialization or debug-mode behavior.
- Do not infer GPU support from the package itself. GPU use depends on the
  user's TensorFlow installation and hardware, not on this layer package.

## Python versions

The repository CI file uses Python 3.9 and 3.10. Python 3.11 also worked in the
inspection environment with TensorFlow 2.15.1. Avoid selecting Python 3.13 for
new environments unless the user's TensorFlow/Keras stack explicitly supports
it.

## Optional example dependencies

The visualization-oriented examples need optional packages beyond the base
package:

```bash
python -m pip install keract matplotlib pydot
```

The model-plotting path also needs the Graphviz `dot` executable available on
`PATH`. Depending on the user's environment, that may come from a system package
manager, Conda package, or preinstalled Graphviz distribution.

Check readiness with:

```bash
python scripts/check_example_dependencies.py
```

## CPU and GPU behavior

The core layer is CPU-capable and does not include custom CUDA/ROCm/MPS kernels.
A CPU-only smoke check is valid for the selected package-use workflows.

TensorFlow may print warnings such as missing CUDA drivers, missing TensorRT, or
failed GPU initialization even when the CPU path succeeds. Treat those messages
as non-blocking for CPU-only tasks. Treat them as blocking only when the user
explicitly requested GPU execution and TensorFlow cannot see or allocate on the
required device.

## Protobuf note

The repository's tox setup sets:

```bash
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
```

If an older TensorFlow/protobuf combination produces protobuf implementation
errors, retrying with this environment variable is evidence-backed. Do not set
it by default for modern environments unless it is needed, because it can affect
protobuf performance.

## Save formats

The original basic example saves to HDF5 (`.h5`) and reloads with
`custom_objects={"Attention": Attention}`. Newer Keras versions may recommend
native `.keras` files instead. For compatibility-sensitive support, test the
exact format the user intends to use with `scripts/smoke_attention.py`.
