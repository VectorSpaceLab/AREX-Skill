# Environment Notes

## Purpose

Read this before installing dependencies or diagnosing imports for this legacy TensorFlow 1.x YOLOv3 repository.

## Repository packaging facts

- The repository is a script checkout, not a packaged distribution: no `setup.py`, `setup.cfg`, or `pyproject.toml` was present.
- Public import roots are top-level packages such as `core` and `mAP` when the working directory or `PYTHONPATH` points at the repository.
- The documented requirements file pins old packages: `numpy==1.15.1`, `Pillow==5.3.0`, `scipy==1.1.0`, `tensorflow-gpu==1.11.0`, `wget==3.2`, and `seaborn==0.9.0`.
- The source uses TensorFlow 1.x symbols including `tf.Session`, `tf.placeholder`, `tf.variable_scope`, `tf.layers.batch_normalization`, `tf.gfile`, and `tf.graph_util.convert_variables_to_constants`.

## Practical dependency guidance

Use a TensorFlow 1.x-compatible Python environment. A CPU inspection environment can validate imports, helper functions, and graph construction, but it does not prove GPU throughput or convergence.

A practical modern fallback for inspection is:

```text
Python 3.7
TensorFlow 1.15.x
protobuf pinned to 3.20.x
NumPy 1.x
OpenCV Python or opencv-python-headless
Pillow
scipy, easydict, tqdm, wget, seaborn when using the repo scripts that import them
```

Why not blindly install `tensorflow-gpu==1.11.0`?

- It is the documented historical requirement, but wheels and CUDA/cuDNN compatibility are old.
- Modern GPUs and drivers may expose hardware that the TF1.11 binary cannot run correctly.
- The repository's training and inference scripts can run on CPU in principle for tiny graph checks, while full training/inference needs real weights/data and a compatible backend.

## TensorFlow/protobuf caveat

TensorFlow 1.15 can fail at import time with recent protobuf versions. The observed error pattern is:

```text
TypeError: Descriptors cannot not be created directly.
```

Fix by pinning protobuf below the 4.x API break, for example:

```bash
python -m pip install 'protobuf==3.20.3'
```

If that is not possible, `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` can be a temporary workaround, but it is slower and should not be the first choice for a stable environment.

## Working-directory caveat

`core.config` stores many paths as relative strings. `core.utils.draw_bbox` has a default argument that reads `cfg.YOLO.CLASSES` during module import, so this can fail before user code executes if `./data/classes/coco.names` is not visible from the current working directory.

Preferred fixes:

1. Run repo scripts from the YOLOv3 working-copy root.
2. Pass explicit paths to bundled skill checkers instead of relying on the source defaults.
3. If writing a reusable wrapper, update config paths before importing `core.utils` or temporarily change into the working-copy root for import-time initialization.

## Headless systems

The demo scripts call GUI/display functions such as `Image.show()`, `cv2.namedWindow`, and `cv2.imshow`. On servers or CI, adapt the workflow to write annotated images or video frames to files instead of opening windows.

## What the bundled checkers prove

- `scripts/check_environment.py` proves Python/TensorFlow importability, basic config path visibility, and optional graph construction.
- Sub-skill checkers validate data formats, conversion prerequisites, PB tensor contracts, training config consistency, and mAP text-format behavior.
- These checks do not download weights, run full training, or prove a legacy CUDA stack.
