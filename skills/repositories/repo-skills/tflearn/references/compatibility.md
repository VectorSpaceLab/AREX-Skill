# Compatibility

Read this before installing TFLearn, debugging imports, or deciding whether a failure is a skill issue versus a legacy runtime issue.

## Verified Runtime Baseline

The generated skill was validated against this public package/runtime shape:

| Component | Verified value | Notes |
| --- | --- | --- |
| TFLearn distribution | `0.5.0` | Source package imports `tensorflow.compat.v1` and disables v2 behavior at import time. |
| TensorFlow | `1.15.5` | Provides the TensorFlow 1.x private/contrib symbols used by the current TFLearn source. |
| Python | `3.7.x` | Chosen because TensorFlow 1.15 wheels are not available for modern Python releases. |
| NumPy | `1.18.x` | Avoids removed aliases such as `np.bool` that appear in legacy code paths. |
| protobuf | `3.20.x` | TensorFlow 1.15 fails with protobuf 4.x descriptor errors. |
| Backend | CPU | Sufficient for selected graph/data/training behavior. CUDA acceleration is optional and not verified by this skill. |

A practical environment usually installs TensorFlow first, then TFLearn:

```bash
python -m pip install "tensorflow==1.15.5" "protobuf==3.20.3" "numpy<1.19" six Pillow h5py scipy pytest
python -m pip install tflearn
```

Use an isolated environment. Do not downgrade protobuf, NumPy, or TensorFlow inside an unrelated modern ML environment unless the user explicitly wants that mutation.

## TensorFlow 2.x Caveat

The package README says to import TensorFlow through `tensorflow.compat.v1`, and the code does call `tf.disable_v2_behavior()`. That is not the same as full compatibility with modern TensorFlow 2.x releases. The current source imports private symbols such as `tensorflow.python.util.nest.is_sequence` and TensorFlow contrib modules in several code paths. Modern TensorFlow versions may remove these symbols.

Common symptom:

```text
ImportError: cannot import name 'is_sequence' from 'tensorflow.python.util.nest'
```

Recommended response:

1. If the user needs to **use TFLearn**, create a legacy TensorFlow 1.15-compatible environment.
2. If the user needs to **port TFLearn code**, treat it as a TensorFlow migration task: replace TFLearn layers/models with Keras/TensorFlow 2 equivalents or patch legacy private imports deliberately.
3. Do not claim that `tf.disable_v2_behavior()` alone makes current TFLearn work on arbitrary TensorFlow 2.x/Python versions.

## protobuf Descriptor Error

Symptom:

```text
TypeError: Descriptors cannot not be created directly.
...
Downgrade the protobuf package to 3.20.x or lower
```

Fix in the TFLearn environment:

```bash
python -m pip install "protobuf==3.20.3"
```

## NumPy Alias Errors

Legacy code uses aliases such as `np.bool`. Modern NumPy removed these aliases. If a user reports `AttributeError: module 'numpy' has no attribute 'bool'`, use one of these approaches:

- Prefer a compatible runtime: `numpy<1.20` for legacy TFLearn use.
- For a porting task, replace `np.bool` with `bool` or `np.bool_` in controlled code.

## Optional Dependencies

TFLearn's core install metadata lists `numpy`, `six`, and `Pillow`. Other workflows need extras:

| Surface | Optional dependency | Notes |
| --- | --- | --- |
| HDF5 feed examples | `h5py` | Needed for HDF5 datasets and TensorFlow 1.15 dependency paths. |
| Image augmentation/SVHN/VAE examples | `scipy` | Some image utilities and examples import SciPy modules. |
| Dask example | `dask` | Optional large-array workflow only. |
| Wide/deep recommender example | `pandas` | Optional tabular recommender workflow. |
| RL Atari example | `gym` plus Atari environment/ROM support | Expensive and environment-specific; not a default smoke target. |
| Plotting/notebooks | `matplotlib`, Jupyter stack | Not required for package API checks. |
| GPU acceleration | historical `tensorflow-gpu` stack with CUDA/cuDNN matching TF1 | Optional; verify actual device placement separately. |

Do not install all optional dependencies by default. Select only the dependencies needed by the user's requested workflow.
