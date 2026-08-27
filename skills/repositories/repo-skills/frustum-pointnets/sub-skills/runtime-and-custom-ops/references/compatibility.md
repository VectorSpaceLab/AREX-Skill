# Compatibility matrix

## Source-era assumptions

The README reports Ubuntu 14.04/16.04, Python 2.7, TensorFlow 1.2/1.4 GPU,
NVIDIA GTX 1080, and at least 8 GB of CPU memory. The code uses TensorFlow 1.x
symbols such as `tf.Session`, `tf.placeholder`, `tf.contrib`, `tf.py_func`,
`tf.to_float`, and `tf.variable_scope`; TensorFlow 2.x will not run it without
a deliberate compatibility port.

The repository also imports `cPickle` directly in data/training modules. On
Python 3, use a controlled source patch:

```python
try:
    import cPickle as pickle
except ImportError:
    import pickle
```

Do not claim that a Python-3 import succeeded if this compatibility change was
only injected at inspection time.

## Verified inspection baseline

A private Python 3.7.16 environment with TensorFlow 1.15.5, NumPy 1.18.5,
SciPy 1.4.1, OpenCV 4.5.5, Pillow 8.4.0, protobuf 3.20.3, and `pip check`
cleanly passed a TensorFlow graph-mode CPU operation. This baseline is useful
for source/API inspection and v1-style CPU graph checks. It is not a proof of
CUDA, custom-op, v2, or performance support.

TensorFlow 1.15 requires protobuf at or below the 3.20 compatibility line in
modern Python environments. If the generated protobuf error says that
Descriptors cannot be created directly, inspect the protobuf version before
trying unrelated code changes.

## Backend decisions

- **CPU:** acceptable for layout parsing, geometry utilities, static API
  inspection, and bounded v1 graph smoke checks.
- **CUDA:** required for the repository's intended v2 custom operators and
  recommended for practical training/inference. Verify TensorFlow's CUDA
  libraries and device list, not only `nvidia-smi`.
- **Mayavi:** optional and GUI-dependent. It is not part of the minimum model
  runtime and often fails over SSH/headless sessions.
- **Python 2:** may be needed for unmodified pickle streams and exact source
  behavior. Keep Python 2 isolated; do not mutate the host interpreter.
