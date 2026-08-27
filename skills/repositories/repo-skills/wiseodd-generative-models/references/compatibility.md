# Compatibility Guide

## Purpose

Read this before claiming that a source artifact from the Generative Models repository can run unchanged. The repository predates the modern TensorFlow 2.x, PyTorch 2.x, and NumPy 2.x stacks.

## Historical baseline

The repository's `environment.yml` records this approximate baseline:

- Python 3.5.1
- NumPy 1.11.0
- SciPy 0.17.1
- scikit-learn 0.17.1
- matplotlib 1.5.3
- Keras 1.1.1 from pip
- TensorFlow and PyTorch installed separately according to the README

This is not a modern reproducible lockfile. Treat it as evidence that the examples are legacy research scripts, not as a recommendation to mutate a current environment.

## Modern-stack blockers observed during generation

| Surface | Modern symptom | Why it matters |
| --- | --- | --- |
| TensorFlow MNIST loader | `ModuleNotFoundError: No module named 'tensorflow.examples'` | The scripts import `tensorflow.examples.tutorials.mnist.input_data`, which is absent from modern TensorFlow 2.x builds. |
| NumPy aliases | `AttributeError: module 'numpy' has no attribute 'float'` or `np.int` | RBM, Helmholtz, and several GAN/VAE PyTorch files still use removed aliases. |
| PyTorch scalar logging | `IndexError: invalid index of a 0-dim tensor` at `loss.data[0]` | Many PyTorch training loops were written before scalar tensors required `.item()` access. |
| MNIST path | file lookup or download failures | Scripts use hard-coded relative paths such as `../../MNIST_data` or `../MNIST_data`. |
| Long training loops | no quick completion signal | Many loops run for 100k to 1M iterations and save samples only periodically. |

## Recommended operating modes

### If the user only needs routing or explanation

Use `references/model-catalog.md` and the family sub-skill references. Do not try to run training just to answer which model family or script label is relevant.

### If the user needs to run unchanged source artifacts

Use `scripts/check_legacy_stack.py --strict` first. If it fails, either create a private legacy-compatible environment or explain the required compatibility patches before attempting a long training run.

### If the user is comfortable patching for a modern stack

Typical minimal patches are:

- Replace `tensorflow.examples.tutorials.mnist.input_data` with a modern MNIST loader such as `tf.keras.datasets.mnist` or a local dataset loader.
- Replace `np.float` with `float` or `np.float64` and `np.int` with `int` or `np.int64`.
- Replace `loss.data[0]` and similar scalar tensor indexing with `loss.item()`.
- Resolve MNIST paths relative to the source file or an explicit user-provided data directory instead of relying on the current working directory.

## Backend notes

No selected capability requires CUDA, ROCm, MPS, or another accelerator. GPU support may speed some PyTorch examples, but the first-order compatibility risks are legacy APIs, dataset paths, and long runtime rather than accelerator availability.

## Bundled checks

Run the diagnostic helper from the skill directory or by absolute path:

```bash
python scripts/check_legacy_stack.py
python scripts/check_legacy_stack.py --strict
```

The helper performs import and compatibility probes only. It does not download MNIST, run training, write model outputs, or mutate the environment.
