# Installation and Compatibility

## When to read

Read this before installing Mask_RCNN, debugging import errors, choosing TensorFlow/Keras versions, or deciding whether to port a workflow to modern Keras.

## Package identity

- Distribution name: `mask-rcnn`.
- Import package: `mrcnn`.
- Version observed in package metadata: `2.1`.
- Primary modules: `mrcnn.config`, `mrcnn.utils`, `mrcnn.model`, `mrcnn.visualize`, `mrcnn.parallel_model`.

## Runtime generation target

The source code asserts TensorFlow `>=1.3` and Keras `>=2.0.8`, but its imports and graph-building patterns are from the TensorFlow 1 / standalone Keras 2 era. A faithful environment should prefer:

```bash
python -m pip install \
  "tensorflow==1.15.5" \
  "Keras==2.3.1" \
  "numpy==1.18.5" \
  "h5py==2.10.0" \
  "scikit-image==0.16.2" \
  "opencv-python==4.5.5.64" \
  "imgaug==0.4.0" \
  "pycocotools==2.0.6"
python -m pip install mask-rcnn
```

If installing from a source checkout, legacy `setup.py` imports pip internals. Newer pip/setuptools build isolation may fail. Prefer an environment with setuptools that still provides `pkg_resources`, and use non-isolated editable install only when inspecting a local checkout:

```bash
python -m pip install "setuptools<70"
python -m pip install --no-build-isolation -e .
```

Do not publish local prefixes or activation commands into task outputs; treat them as private setup details.

## Modern TensorFlow/Keras caveats

A modern TensorFlow 2.x environment can import some TensorFlow operations, but Mask_RCNN may fail before usable model construction because:

- `keras.engine` is no longer a public standalone import in recent Keras.
- TF1 aliases such as `tf.log`, `tf.random_shuffle`, `tf.to_float`, and `tf.reset_default_graph` moved or changed.
- Keras dynamic-shape handling can reject legacy `Reshape((s[1], num_classes, 4))` where `s[1]` is `None`.

For a task that must run under modern Keras, first decide whether the deliverable is a **porting task**. A port usually needs source edits or a maintained fork; do not promise that a small import shim makes training/inference verified.

## CPU and GPU expectations

- CPU is sufficient for imports, API inspection, dataset validation, mask conversion, and tiny graph-build smoke checks.
- Real training is normally GPU-oriented. The Shapes tutorial states that CPU training is too slow for the ResNet backbone.
- Multi-GPU support is implemented by `mrcnn.parallel_model.ParallelModel`, but it is TensorFlow/Keras graph-mode code and should be verified with the exact CUDA/cuDNN/TensorFlow stack before use.
- When using CPU only, set `GPU_COUNT = 1` and `IMAGES_PER_GPU = 1` or another value your memory can handle.

## Minimal import and graph-build checks

Use the bundled diagnostic before deeper workflows:

```bash
python scripts/check_env.py --show-signatures
python scripts/check_env.py --build-tiny-graph
```

A tiny graph build verifies model construction, not weight compatibility, data correctness, training speed, or numerical quality.

## Optional dependencies by workflow

| Dependency | Needed for |
| --- | --- |
| `pycocotools` | COCO dataset loading, COCO result encoding, official COCO evaluation. |
| `opencv-python` | Shapes synthetic drawing and video color splash helpers. |
| `imgaug` | Training augmentations in COCO/nucleus examples and `load_image_gt` augmentation path. |
| `IPython`/Jupyter | Original notebook exploration only; not required for script/API use. |
| CUDA-enabled TensorFlow | GPU training/inference acceleration and multi-GPU tests. |

Install only the dependencies required by the selected workflow. Do not install all extras or download weights/datasets just to validate dataset schemas or package APIs.
