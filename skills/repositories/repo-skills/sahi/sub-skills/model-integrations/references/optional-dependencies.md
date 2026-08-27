# Optional dependencies for SAHI model wrappers

SAHI's base install is intentionally light. Detector frameworks are optional and must match the selected `model_type`, device, Python version, and weight format.

## Verification status for this generated skill

Source, docs, tests, and package metadata were inspected. Optional detector dependencies were intentionally not all installed during construction. In particular, MMDetection and TorchVision wrappers should be treated as source-backed until verified in the target runtime. Run the bundled checker before debugging model load failures:

```bash
python ../scripts/check_model_dependencies.py
```

From this `references/` directory, the same checker is at `../scripts/check_model_dependencies.py`; from the sub-skill root, use `scripts/check_model_dependencies.py`.

## Package extras declared by SAHI

| Extra or install target | Packages declared | Model routes it helps | Notes |
| --- | --- | --- | --- |
| Base install | Core image/geometry/CLI packages only. | No detector wrapper is guaranteed. | You still need a framework such as Ultralytics, TorchVision, HuggingFace Transformers, etc. |
| `sahi[torch]` | `torch` | Shared device dependency. | Needed by most wrappers even for CPU inference. Choose CPU/CUDA/MPS builds deliberately. |
| `sahi[ultralytics]` | `ultralytics` | `ultralytics`, aliases `yolov8`/`yolov11`/`yolo11`/`yolo26`, `yoloe`, `yolo-world`, `rtdetr`. | RT-DETR in this SAHI source uses Ultralytics, not HuggingFace. |
| `sahi[yolov5]` | `yolov5` | `yolov5`. | The wrapper also requires torch. |
| `sahi[transformers]` | `transformers` on supported Python versions. | `huggingface`, `huggingface_segmentation`. | Many checkpoints also need torch and model-specific extras such as `timm`. GroundingDINO requires a sufficiently new Transformers release. |
| `sahi[torchvision]` | `torch`, `torchvision` | `torchvision`; also useful for some postprocess acceleration. | Torch and TorchVision versions must be compatible. |
| `sahi[roboflow]` | `inference`, `rfdetr` on supported Python versions. | `roboflow` Universe and local RF-DETR. | Declared for newer Python only; Universe mode needs an API key, local RF-DETR does not. |
| `sahi[onnx]` | `onnx`, `onnxruntime` on supported Python versions. | Ultralytics exported ONNX models and ONNX checks. | This does not replace `ultralytics`; it supports exported model runtime behavior. |
| `sahi[numba]` | `numba` on supported Python versions. | Postprocess acceleration only. | Not a model loader dependency; route postprocess decisions elsewhere. |
| `sahi[all]` | Most declared optional dependencies except project-specific stacks. | Broad local testing. | Avoid as a first install in constrained environments; install only what the selected route needs. |
| MMDetection stack | Not declared as a SAHI extra in inspected metadata. | `mmdet`. | Install `torch`, `mmdet`, `mmcv`, and `mmengine` as a compatible OpenMMLab stack. |
| Detectron2 | Not declared as a SAHI extra in inspected metadata. | `detectron2`. | Install a wheel/source build compatible with Python, torch, CUDA, and platform. |

## Dependency warning map

| Package group | Why it matters | Common failure shape | Action |
| --- | --- | --- | --- |
| `torch` | Device selection, tensors, and most framework models. | Explicit `device="cuda:0"` or `"mps"` fails when torch is absent; wrappers requiring torch fail before loading weights. | Install the correct torch build for CPU/CUDA/MPS and verify backend availability before model load. |
| `torchvision` | TorchVision wrapper and optional GPU postprocess backend. | `ImportError` for `torchvision` or torch/torchvision ABI mismatch. | Install versions that match the torch build; check both package importability and actual model construction. |
| `ultralytics` | Ultralytics YOLO, YOLOE, YOLO-World, and SAHI RT-DETR wrapper. | Missing `ultralytics`, unsupported YOLOE/YOLO-World class, missing local weights, or implicit download attempt. | Install a recent Ultralytics version and use local weights for offline work. For exported ONNX models, also check `onnxruntime`. |
| `yolov5` | Classic YOLOv5 wrapper. | Missing `yolov5` or invalid YOLOv5 model object/module. | Install the `yolov5` package and pass a YOLOv5-supported weight source. |
| `transformers` / `timm` | HuggingFace object detection, GroundingDINO, MaskFormer/Mask2Former/OneFormer. | Missing `transformers`, too old Transformers for GroundingDINO, or missing backbone dependencies such as `timm`. | Install Transformers for the Python version and add checkpoint-specific extras. Use `token`/`HF_TOKEN` for private or gated models. |
| `mmdet` / `mmcv` / `mmengine` | MMDetection wrapper imports these at module import time. | Immediate import failure before any `MmdetDetectionModel` object is created. | Install a mutually compatible OpenMMLab stack for the selected torch/CUDA/Python combination. |
| `detectron2` | Detectron2 model-zoo/local config wrapper. | No wheel for the platform or mismatch with torch/CUDA. | Use a compatible wheel or source build; isolate it if it conflicts with other detector stacks. |
| `inference` | Roboflow Universe hosted model route. | Missing `inference` or authorization failure. | Install the SDK and provide `api_key` or `ROBOFLOW_API_KEY`; do not confuse hosted ids with local RF-DETR class names. |
| `rfdetr` | Local RF-DETR route under the Roboflow wrapper. | Missing `rfdetr`, unresolved local class name, missing custom category mapping, or wrong resolution. | Pass an exact RF-DETR class name/class/instance; provide local weights and `category_mapping` for custom classes. |
| `onnxruntime` | Runtime for many exported ONNX detector weights. | Ultralytics model path is `.onnx` but runtime cannot execute it. | Install `onnxruntime` for CPU or a provider-specific package as appropriate. |
| `numba` | Optional postprocess acceleration. | No effect on model import; only affects backend speed/selection. | If missing, route to postprocess backend guidance rather than changing model_type. |

## Safe dependency inspection

The bundled checker uses only `importlib.util.find_spec` and `importlib.metadata`. It reports import-spec visibility and installed distribution versions without importing heavy detector modules, downloading weights, or touching credentials:

```bash
python ../scripts/check_model_dependencies.py --model-type huggingface
python ../scripts/check_model_dependencies.py --model-type roboflow --json
```

Treat a green checker result as "packages appear present", not as proof that a specific checkpoint can load. A final model load still depends on weights, configs, credentials, device availability, and framework version compatibility.
