# Compatibility and Installation

Read this before running Keras-GAN model scripts. The repository is a stale collection of standalone Keras files, not a Python package with setup metadata or console entry points.

## Verified compatibility family

Private inspection verified representative imports and constructor smokes with this legacy stack family:

| Component | Compatible family |
| --- | --- |
| Python | 3.7-era interpreter |
| TensorFlow backend | TensorFlow 1.15.x |
| Keras | standalone Keras 2.2.x |
| keras-contrib | 2.0.x from the historical keras-team repository |
| NumPy | 1.18.x |
| SciPy | 1.2.x, because `scipy.misc.imread` and `scipy.misc.imresize` still exist |
| Matplotlib | non-interactive backend recommended for scripts and CI |
| Pillow / scikit-image | installed for image handling and PixelDA resizing support |
| h5py / protobuf | h5py below 3 and protobuf below 3.21 avoid common TensorFlow 1.x failures |

Use this as a compatibility target, not as a general recommendation for new projects. For modern production work, port the scripts deliberately and test the port.

## Installation approach

The upstream README says to install `requirements.txt`, but that file does not pin versions and includes a git dependency for keras-contrib. A faithful legacy environment should pin versions rather than installing latest packages.

Example dependency intent:

```text
tensorflow==1.15.5
Keras==2.2.4
numpy<1.19
scipy<1.3
matplotlib
pillow
scikit-image
h5py<3
protobuf<3.21
git+https://www.github.com/keras-team/keras-contrib.git
```

Do not run this in a user-owned environment without approval. Prefer a scratch environment because TensorFlow 1.x and modern ML packages often conflict.

## Minimal runtime check

From this generated skill root, run:

```bash
python scripts/check_legacy_runtime.py
```

Success should report TensorFlow, Keras, backend, NumPy, SciPy, Matplotlib, Pillow, scikit-image, and keras-contrib availability. Use `--json` for machine-readable output.

The checker does not import the original Keras-GAN source files and does not prove that full training will run. It only diagnoses the dependency family.

## Importing source scripts safely

Because the repo is not a package, model code is normally loaded by file path or by running from each model directory. Scripts such as CycleGAN and Pix2Pix import a sibling `data_loader.py` with `from data_loader import DataLoader`, so a direct import from another directory can fail unless the workflow directory is on `sys.path`.

Safe patterns:

- Use the sub-skill helpers that accept `--repo-root` or dataset roots.
- For manual imports, add the selected script directory to `sys.path` temporarily.
- Avoid running a script's `__main__` block unless the user explicitly requested training and accepted side effects.

## GPU and backend notes

The repository does not expose separate CUDA-only APIs. GPU is useful for long training, but the safe operating checks in this skill are CPU-compatible. Do not install a GPU stack merely to inspect or validate datasets.

If a user wants full training on GPU, verify TensorFlow 1.x GPU compatibility separately. CUDA, cuDNN, driver, and Python wheel compatibility are much stricter for TensorFlow 1.x than for modern frameworks.

## Modern-port guidance

If the task is to port Keras-GAN code to modern Keras/TensorFlow:

1. Replace standalone `keras` imports consistently rather than mixing `keras` and `tensorflow.keras`.
2. Replace `keras_contrib.layers.normalization.InstanceNormalization` with an equivalent maintained layer.
3. Replace `scipy.misc.imread` and `scipy.misc.imresize` with Pillow or scikit-image while preserving RGB conversion, resizing, dtype, and normalization.
4. Replace graph/session backend calls such as `K.gradients` or private `_Merge` usages with supported custom layers or `tf.GradientTape` where appropriate.
5. Parameterize dataset names, paths, output directories, and epoch counts before adding tests.
