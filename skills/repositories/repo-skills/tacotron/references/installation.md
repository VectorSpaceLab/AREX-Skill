# Installation and compatibility

## When to read

Read this before importing the repository, running a CLI, or diagnosing an
error caused by Python, TensorFlow, NumPy, SciPy, librosa, or Falcon.

## Evidence-backed baseline

This checkout has no Python packaging metadata. Its `requirements.txt` pins:
Falcon 1.2.0, inflect 0.2.5, librosa 0.5.1, matplotlib 2.0.2, NumPy 1.14.3,
SciPy 0.19.0, tqdm 4.11.2, and Unidecode 0.4.20. TensorFlow is intentionally
omitted because the original README expects the user to select a platform
specific install.

A verified inspection baseline used Python 3.6.13, TensorFlow 1.15.5, NumPy
1.16.6, SciPy 0.19.0, librosa 0.5.1, Falcon 1.2.0, and the remaining pinned
packages. The NumPy and llvmlite pins were necessary for the old SciPy/librosa
and numba stack; a current resolver may otherwise select incompatible versions.

```bash
CHECKOUT_ROOT=/path/to/tacotron-checkout
cd "$CHECKOUT_ROOT" && python -m pip install -r requirements.txt
# Choose the TensorFlow 1.x wheel appropriate for the host and CUDA policy.
cd "$CHECKOUT_ROOT" && python -c "import tensorflow as tf; print(tf.__version__)"
cd "$CHECKOUT_ROOT" && python -m pip check
```

Do not install TensorFlow 2.x for this source without a deliberate port: the
model imports `tf.contrib.rnn`, `tf.contrib.seq2seq`,
`tf.contrib.training.HParams`, and other removed APIs.

## Import checks

Run the native import check from the actual Tacotron checkout root (not the
skill root), with the source root on Python's import path:

```bash
CHECKOUT_ROOT=/path/to/tacotron-checkout
cd "$CHECKOUT_ROOT" && python -c "import tensorflow, librosa; import text, models, synthesizer; print(tensorflow.__version__)"
```

If `librosa` fails during import, inspect the versions of `numpy`, `scipy`,
`numba`, and `llvmlite` together. Do not solve one mismatch by upgrading the
entire stack without checking TensorFlow's NumPy upper bound.

GPU TensorFlow can accelerate training and synthesis, but GPU is an optional
performance path in this repository's public setup notes. A CPU environment is
sufficient for text tests, CLI parsing, graph/API inspection, and small fixture
checks. Do not claim GPU runtime verification from a CPU import.
