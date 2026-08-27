# Installation and Optional Dependencies

## When to read

Read this before installing SAHI for a task that names a detector framework, GPU/MPS/CUDA, COCO evaluation, FiftyOne visualization, ONNX, numba postprocessing, HuggingFace/Roboflow services, or a specific `model_type`.

## Base install

```bash
pip install sahi
python -c "import sahi; print(sahi.__version__)"
```

Base SAHI installs the core package dependencies used for slicing, annotation/result objects, numpy postprocessing, image I/O, plotting, YAML/JSON helpers, and the CLI entry point. It does **not** install detector frameworks or model weights.

## Python and package facts

- Public distribution name: `sahi`.
- Public import package: `sahi`.
- Console entry point: `sahi`.
- Supported Python range in package metadata: `>=3.8`.
- Construction-time inspection verified the base package and core APIs on Python 3.11.
- Base postprocessing falls back to the numpy backend when neither numba nor torch/torchvision GPU acceleration is available.

## Optional extras and common framework installs

Install only the framework needed for the selected task. Avoid `sahi[all]` unless a user explicitly wants a broad multi-framework environment.

| Need | Install direction | Notes |
| --- | --- | --- |
| Ultralytics YOLO/YOLO11/YOLO26, YOLOE, YOLO-World, RT-DETR via Ultralytics | `pip install "sahi[ultralytics]"` or `pip install sahi ultralytics` | Model weights such as `.pt`, `.onnx`, or model names are separate. ONNX exports also need ONNX/ONNX Runtime. |
| Torch device utilities or TorchVision postprocess/model support | Install a torch/torchvision pair for the target CPU/CUDA/MPS platform; `pip install "sahi[torchvision]"` is a CPU-friendly baseline unless you choose a CUDA wheel index explicitly | Do not count a CPU-only torch import as proof that CUDA inference works. |
| HuggingFace object detection, GroundingDINO, segmentation | `pip install "sahi[transformers]" timm` | Private/gated models may need `token=` or `HF_TOKEN`. GroundingDINO needs text labels or prompts. |
| YOLOv5 pip package route | `pip install "sahi[yolov5]"` | Older YOLOv5/package combinations can be version-sensitive; prefer Ultralytics route when appropriate. |
| Roboflow Universe or local RF-DETR | `pip install "sahi[roboflow]"` on supported Python/platforms | Universe ids need `api_key=` or `ROBOFLOW_API_KEY`; local RF-DETR class-name routes need the RF-DETR package and custom category mapping for custom classes. |
| ONNX model loading/export | `pip install "sahi[onnx]"` | The detector framework still controls ONNX runtime behavior. |
| numba postprocessing | `pip install "sahi[numba]"` or `pip install numba` | First call may JIT-compile; numpy remains the fallback. |
| COCO evaluation or error analysis | `pip install pycocotools` | `sahi coco evaluate` and `sahi coco analyse` need COCO evaluator packages beyond the base install. |
| FiftyOne visualization | `pip install fiftyone` | Interactive UI/session behavior depends on the local environment. |
| MMDetection | Follow OpenMMLab/MMDetection install guidance for compatible `torch`, `mmcv`, `mmengine`, and `mmdet` | SAHI metadata does not provide a simple MMDetection extra; Python, torch, CUDA, and OpenMMLab versions must match. |
| Detectron2 | Install Detectron2 wheels/builds matching Python, torch, platform, and CUDA/CPU | Linux/wheel compatibility is a common blocker. |

## GPU and backend policy

- Use `device="cpu"` for deterministic offline checks and CI-like smoke tests.
- Use `device="cuda:0"` only after a target environment proves torch/framework CUDA availability with a tiny device operation.
- SAHI postprocessing auto-selection prefers torchvision only when torchvision and CUDA/MPS are available; otherwise it chooses numba if installed, then numpy.
- To avoid ambiguous backend selection while debugging, pin the backend:

```python
from sahi.postprocess.backends import set_postprocess_backend
set_postprocess_backend("numpy")
```

## Install validation

Run the bundled checker from the root of this generated skill:

```bash
python scripts/check_sahi_env.py
python sub-skills/model-integrations/scripts/check_model_dependencies.py
```

For a no-model smoke path, run the synthetic scripts listed in the root `SKILL.md`. They validate package plumbing and data structures, not detector accuracy or model downloads.

## OpenCV note

SAHI imports OpenCV through `cv2`. Mixing multiple OpenCV distributions at different versions can break import with confusing `cv2` attribute errors. Keep one OpenCV distribution or reinstall all installed OpenCV variants at the same version.
