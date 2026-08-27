# Compatibility and Installation Reference

Read this before recreating a runtime for this repository. The project was
written for TensorFlow 2.3-era APIs and old dependency pins, so modern Python or
GPU stacks often fail even when the code is correct.

## Package style

- The repository is script-style and does not ship `setup.py` or `pyproject.toml`.
- The import root is `core/`; scripts import modules such as `core.yolov4`,
  `core.utils`, `core.dataset`, and `core.config`.
- Run Python commands from a target checkout root, or set `PYTHONPATH` to that
  checkout root, because `core.config` defaults to relative paths such as
  `./data/classes/coco.names`.

## Recommended reconstruction target

Use an isolated Python 3.8 environment when possible:

```bash
python -m pip install "tensorflow==2.3.0" "opencv-python==4.1.2.30" \
  "protobuf<3.20" lxml tqdm absl-py easydict matplotlib pillow
```

Why this differs from the upstream requirements:

- The README/requirements pin TensorFlow 2.3.0rc0, but that release candidate
  may no longer be available for current package indexes. TensorFlow 2.3.0
  stable is the closest tested replacement for basic CPU imports and CLI help.
- `opencv-python==4.1.1.26` may be unavailable; `opencv-python==4.1.2.30` keeps
  the same major/minor era and passed import checks during skill construction.
- TensorFlow 2.3 fails with modern protobuf 4/5 using errors like
  `Descriptors cannot be created directly`; pin `protobuf<3.20` or use the
  slower `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` workaround only as a
  temporary diagnostic.

If the user needs exact historical reproduction, prefer a frozen environment or
container from the time of TensorFlow 2.3 rather than upgrading random packages.

## CPU, GPU, and TensorRT expectations

| Capability | Backend expectation | Notes |
|---|---|---|
| Config import, class list, CLI help | CPU | Enough for command planning and static checks. |
| SavedModel/TFLite conversion | CPU can work | Full YOLOv4 conversion still needs real weights and memory. |
| Image/video inference | CPU can work | GPU improves speed but is not required for correctness. |
| Training | CPU technically possible but usually impractical | GPU recommended; training quality is not fully reproduced in README. |
| TF-TRT conversion | NVIDIA GPU + TensorRT/CUDA stack | CPU is not a substitute. TensorFlow 2.3 expects old CUDA/cuDNN libraries. |
| Android app | Android SDK/device/emulator; optional GPU/NNAPI delegates | Python environment is not enough. |

TensorFlow 2.3 GPU wheels expect CUDA 10.1-era runtime libraries and cuDNN 7.
A modern driver can expose GPUs while TensorFlow still logs missing libraries
such as `libcudart.so.10.1`, `libcublas.so.10`, or `libcudnn.so.7` and then
reports no usable GPU devices. Treat that as an optional GPU/TensorRT block,
not as a failure of CPU command planning.

## Minimal validation sequence

From the target checkout root after installing dependencies:

```bash
python - <<'PY'
import tensorflow as tf
import cv2
from core.config import cfg
from core import utils
print(tf.__version__)
print(cv2.__version__)
print(cfg.YOLO.CLASSES)
print(len(utils.read_class_names(cfg.YOLO.CLASSES)))
print(tf.config.experimental.list_physical_devices("GPU"))
PY
```

If the command succeeds and prints 80 classes for the default COCO file, the
core Python dependency layer is usable for this repo's CPU workflows.

## Known version-sensitive code paths

- `core.dataset.Dataset.preprocess_true_boxes` uses `np.float`, which is removed
  in recent NumPy. TensorFlow 2.3 normally constrains NumPy to 1.18.x, where the
  alias still exists.
- Scripts use `tensorflow.compat.v1.ConfigProto` and `InteractiveSession` even
  under TensorFlow 2.x.
- `convert_trt.py` imports `tensorflow.python.compiler.tensorrt.trt_convert`;
  that path depends on the TensorFlow build and TensorRT runtime.
- `convert_trt.py` contains a typo `utils.image_preporcess` in its INT8
  representative-data function. FP16/FP32 conversion paths do not call that
  function, but INT8 TF-TRT calibration will fail until corrected in a target
  checkout.
