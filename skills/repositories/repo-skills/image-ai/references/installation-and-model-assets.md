# Installation and Model Assets

## Purpose

Read this before installing ImageAI, choosing CPU/GPU dependencies, or deciding whether a model file can be used with ImageAI 3.x.

## ImageAI 3.x backend

ImageAI 3.x uses PyTorch for the active `imageai` package. The current package path covers:

- ImageNet classification: MobileNetV2, ResNet50, InceptionV3, DenseNet121.
- COCO object detection: RetinaNet, YOLOv3, TinyYOLOv3.
- Video detection with the same COCO model families.
- Custom classification and custom YOLO/TinyYOLO detection training/inference.

TensorFlow/Keras `.h5` pretrained or custom models belong to legacy ImageAI 2.1.6-or-earlier workflows. Current ImageAI 3.x extension checks reject `.h5` and require `.pt` or `.pth` PyTorch weights.

## Python and dependencies

The project documentation targets Python 3.7 through 3.10 for ImageAI 3.x. For modern environments, prefer a Python version that has compatible PyTorch, torchvision, OpenCV, SciPy, and Pillow wheels.

Typical runtime dependencies:

```bash
pip install cython "pillow>=7.0.0" "numpy>=1.18.1" "opencv-python>=4.1.2" \
  "torch>=1.9.0" "torchvision>=0.10.0" pytest tqdm scipy matplotlib mock
pip install imageai
```

Install PyTorch with the wheel index appropriate to the runtime:

- CPU-only or generic CPU verification: a CPU-capable PyTorch/torchvision pair is enough.
- CUDA acceleration: install a CUDA-enabled PyTorch/torchvision pair compatible with the NVIDIA driver and Python version.
- Do not install GPU packages just because a GPU exists; require them when the user wants accelerated inference/training or a verification case specifically needs CUDA.

`pycocotools` is listed as an extra in the repository, but the active ImageAI 3.x PyTorch custom YOLO training path covered by this skill does not import it. Avoid installing it unless a user specifically works with legacy/deprecated TensorFlow/COCO evaluation code outside this skill's selected scope.

## Model asset expectations

ImageAI does not ship pretrained weights with the package. The user must supply local files:

| Workflow | Required local assets |
| --- | --- |
| ImageNet classification | One `.pt`/`.pth` weight file matching MobileNetV2, ResNet50, InceptionV3, or DenseNet121; one image input. |
| Custom classification | Trained `.pt`/`.pth` classifier plus matching `<dataset>_model_classes.json`; one image input. |
| COCO image/video detection | RetinaNet `.pth`, YOLOv3 `.pt`, or TinyYOLOv3 `.pt` COCO weights; image or video/camera input. |
| Custom image/video detection | Custom YOLOv3/TinyYOLOv3 `.pt`/`.pth` weights plus matching `*_detection_config.json` containing labels and anchors. |
| Custom training | Dataset in the required layout; optional compatible transfer `.pt`/`.pth` weights; enough CPU/GPU compute for the chosen run. |

Keep model type and asset type aligned:

- `setModelTypeAsResNet50()` must use ResNet50 weights, not DenseNet or Inception weights.
- Standard COCO `ObjectDetection` can use RetinaNet, YOLOv3, or TinyYOLOv3.
- `CustomObjectDetection` and `CustomVideoObjectDetection` support YOLOv3 or TinyYOLOv3 custom models, not RetinaNet.
- Custom detection JSON must come from the same training run or an equivalent class/anchor configuration as the model checkpoint.

## Quick environment smoke

Use the bundled root checker before loading weights:

```bash
python scripts/check_imageai_env.py
python scripts/check_imageai_env.py --require-cuda
```

The checker imports ImageAI, PyTorch, and torchvision, constructs key ImageAI classes, prints important signatures, and optionally verifies a CUDA tensor allocation. It does not load model weights, download data, open cameras, or start training.

## CPU vs CUDA guidance

- CPU is sufficient for import checks, API signature inspection, dataset validation, Pascal VOC conversion, and tiny smoke tests.
- CPU can run image inference but may be slow for large models.
- CUDA is strongly recommended for full video detection and realistic training.
- If CUDA is unavailable, do not claim video/training throughput has been verified. Use CPU only for semantic/API checks or bounded tiny fixtures.
- Call `useCPU()` before `loadModel()` when forcing CPU in classification or detection APIs.

## Legacy TensorFlow guidance

If a user only has `.h5` files:

1. Explain that ImageAI 3.x rejects `.h5` because the active backend is PyTorch.
2. Prefer retraining or converting to ImageAI 3.x PyTorch artifacts when possible.
3. If the user must run the legacy artifact, isolate a legacy environment with ImageAI 2.1.6 or earlier and TensorFlow/Keras versions compatible with that release. Do not mix legacy TensorFlow assets into the ImageAI 3.x PyTorch package workflow.
