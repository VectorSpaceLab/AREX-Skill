# Install and Build Notes

## Purpose

Read this when a tf-faster-rcnn checkout will not set up cleanly, when `lib/setup.py` or `lib/Makefile` fails, or when you need a compact recipe for the legacy Python / TensorFlow / CUDA environment that this repository expects.

## Verified baseline

The source and inspection environment agree on these facts:

- The code is legacy TensorFlow 1.x era. The README says the project follows the `r1.2` format.
- The repository root is not a Python package. The build entry point is `lib/setup.py`, not a top-level `setup.py`.
- `lib/Makefile` runs `python setup.py build_ext --inplace` and then removes the temporary `build/` directory.
- `lib/setup.py` hard-detects CUDA at import/build time and builds three extensions: `utils.cython_bbox`, `nms.cpu_nms`, and `nms.gpu_nms`.
- `lib/setup.py` looks for `CUDAHOME` first and falls back to `nvcc` on `PATH`.
- The default GPU NMS path is enabled by `cfg.USE_GPU_NMS = True`.
- The verified CPU inspection environment used Python 3.7 with `tensorflow==1.15.5` and `protobuf==3.20.3` as a compatible legacy inspection substitute.

## Practical setup order

1. Create an isolated Python environment.
2. Install the core Python dependencies.
3. Verify TensorFlow 1.x and `tensorflow.contrib.slim` import cleanly.
4. Run the bundled environment inspector.
5. Only then try native compilation from `lib/` if you actually have CUDA available.

A representative inspection-friendly package set is:

- `numpy`
- `scipy`
- `easydict`
- `PyYAML`
- `Cython`
- `opencv-python-headless`
- `Pillow`
- `matplotlib`
- `tensorflow==1.15.5`
- `protobuf==3.20.3`
- `pycocotools` for COCO workflows

## Build prerequisites

The native build path needs:

- `nvcc`
- a real CUDA toolkit root with `include/` and `lib64/`
- a compiler that matches that CUDA toolkit
- a `-arch=sm_*` flag in `lib/setup.py` that matches your GPU

The README shows example `sm_` values for several common cards. If your GPU does not match the default `-arch=sm_52`, edit the flag before building.

### Important CUDA variable detail

`lib/setup.py` checks `CUDAHOME`, not just `CUDA_HOME`.

If your environment only exports `CUDA_HOME`, either:

- also export `CUDAHOME`, or
- put `nvcc` on `PATH` so `setup.py` can find it directly.

## What a successful smoke path looks like

The safe inspection path is complete when all of these are true:

- the core Python dependencies import
- `tensorflow.contrib.slim` imports
- `model.config` imports from `lib/`
- `generate_anchors()` returns shape `(9, 4)`
- `py_cpu_nms` keeps the expected tiny synthetic fixture indices `[0, 2]`
- optional CUDA and compiled NMS checks may still be missing if you are intentionally staying CPU-only

## CPU-only inspection path

If you do not have CUDA available, you can still inspect:

- `lib/model/config.py`
- `lib/layer_utils/generate_anchors.py`
- `lib/nms/py_cpu_nms.py`
- `experiments/cfgs/*.yml`

That is enough for source-level reasoning, but it does **not** make the full runtime import path ready because `model.nms_wrapper` imports the compiled `nms.gpu_nms` module eagerly.

## Historical Docker notes

The Dockerfiles in `docker/` are reference material only. They show an old CUDA 7.5 / 8.0 container shape with Python and TensorFlow GPU packages, but they are not a maintained modern install path.

## Do not do here

- Do not install datasets or checkpoints.
- Do not start demo, training, or evaluation runs.
- Do not treat the repository root as a pip-installable package.
- Do not assume `cfg.USE_GPU_NMS=False` removes the compiled NMS import requirement.
