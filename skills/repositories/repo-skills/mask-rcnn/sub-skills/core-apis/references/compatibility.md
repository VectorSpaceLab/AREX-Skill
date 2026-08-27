# Core Compatibility Notes

## Legacy code surface

Mask_RCNN is a TensorFlow graph-mode, standalone Keras 2 implementation. The code imports `tensorflow as tf`, `keras`, `keras.backend`, `keras.layers`, `keras.engine`, and `keras.models` directly. It also uses symbols that are TF1-era names, including `tf.log`, `tf.random_shuffle`, and `tf.to_float`.

## Recommended execution path

For faithful execution, use a TensorFlow 1.15.x and Keras 2.3.x stack. This combination supports the import layout and graph semantics expected by the package.

A tiny graph-build check should:

- import `mrcnn.model` without Keras import errors;
- create a `Config` subclass with dimensions divisible by 64;
- construct `MaskRCNN(mode="inference", ...)`;
- report model name `mask_rcnn` with three inference inputs and seven outputs.

Run:

```bash
python sub-skills/core-apis/scripts/inspect_mask_rcnn_api.py --build-tiny-graph
```

## Modernization signals

Treat the following as signs that the user is not simply using the package but porting it:

- `ModuleNotFoundError: No module named 'keras.engine'`.
- `AttributeError: module 'tensorflow' has no attribute 'log'`.
- Keras 3 or TensorFlow 2 eager-mode errors during model construction.
- Dynamic reshape failures where a target shape contains `None`.
- Requests to use `tf.keras`, Keras 3, Python 3.11+, or current CUDA wheels.

For a port, update imports, replace TF1 aliases with `tf.compat.v1` or TF2 equivalents, review every custom Keras layer (`ProposalLayer`, `PyramidROIAlign`, `DetectionTargetLayer`, `DetectionLayer`), and rerun actual graph-build plus workflow smoke tests. Do not claim training/inference compatibility based on import success only.

## Backend criticality

- Required for this skill's verified operating scope: CPU import, API signature inspection, data helpers, and tiny graph build.
- Optional: CUDA training/inference acceleration and `ParallelModel` multi-GPU support. These require exact TensorFlow/CUDA/cuDNN compatibility and should be verified on the user's host before operational claims.
- Alternative: For purely data-format or command-planning tasks, no TensorFlow graph build is needed; package import or bundled scripts may be enough.

## Config shape constraints

The model build checks that image height and width are divisible by `2**6`. Use dimensions such as 128, 256, 512, or 1024 when creating smoke configs. `pad64` can pad inference images to multiples of 64; `crop` is training-only.

## Python package name traps

- `pip install mask-rcnn` installs a distribution named `mask-rcnn`, but Python imports `mrcnn`.
- The source setup file has legacy pip parsing logic. When installing from source with modern pip, build isolation can fail before dependencies are resolved.
- If `pkg_resources` is missing in a very new setuptools-only environment, installing `setuptools<70` restores the legacy API.
