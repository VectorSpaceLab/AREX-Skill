---
name: export-and-deployment
description: "Export, benchmark, and route Ultralytics YOLO models to deployment
  formats including ONNX, OpenVINO, TensorRT, CoreML, TFLite, Triton, and edge
  runtimes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Export And Deployment

Use this sub-skill when the user needs `model.export()`, `yolo export`, `yolo benchmark`, backend dependency choices, or deployment-format routing for Ultralytics YOLO models. It covers export/deploy decisions only; route data YAML setup to `data-and-configuration`, training and validation to `training-and-validation`, prediction result handling to `inference-and-results`, model-family selection to `model-families-and-tasks`, and repo/test maintenance to `repo-development`.

## Fast Routing

- **Portable CPU/server deployment:** prefer `format=onnx`; it is handled by the `export-base` extra and can be used through ONNX Runtime, OpenCV DNN (`dnn=True`), or Triton.
- **Intel CPU/GPU/NPU deployment:** prefer `format=openvino`; use `device=intel:cpu`, `device=intel:gpu`, or `device=intel:npu` when running exported models.
- **NVIDIA GPU deployment:** prefer `format=engine` for TensorRT; export and inference require compatible CUDA/NVIDIA runtime, and INT8 calibration should happen on the target GPU class.
- **Apple apps:** prefer `format=coreml`; export on macOS or x86 Linux, but Ultralytics CoreML predict/val execution is macOS-only.
- **Mobile/embedded TensorFlow:** prefer `format=tflite` or `format=edgetpu`; these use TensorFlow export tooling and often require pinned dependency environments.
- **Benchmark comparison:** use `yolo benchmark model=... data=... imgsz=... format=...` for one target, or omit `format` to attempt all supported formats that work in the current environment.

## Command Shapes

Ultralytics CLI commands use `yolo TASK MODE arg=value`; `TASK` is optional for export/benchmark when the model implies it.

```bash
yolo export model=yolo26n.pt format=onnx imgsz=640 dynamic=True
yolo export model=best.pt format=engine device=0 half=True workspace=4
yolo benchmark model=yolo26n.pt data=coco8.yaml imgsz=640 format=onnx
yolo predict model=yolo26n.onnx source=image.jpg
```

Python API equivalents:

```python
from ultralytics import YOLO

model = YOLO("yolo26n.pt")
path = model.export(format="onnx", imgsz=640, dynamic=True)
metrics = YOLO(path).val(data="coco8.yaml")
```

Before suggesting a command that might download weights, export large artifacts, pull containers, train, benchmark all formats, or touch media, call out the side effect and offer a dry-run plan first. For a safe local plan, use `scripts/plan_export.py`.

## Important Export Arguments

- `format`: export target such as `onnx`, `openvino`, `engine`, `coreml`, `saved_model`, `pb`, `tflite`, `edgetpu`, `tfjs`, `mnn`, `ncnn`, `imx`, `rknn`, `executorch`, `axelera`, `deepx`, or `qnn`.
- `imgsz`: export input size; benchmark mode requires square image size.
- `device`: CPU/GPU/backend selector; TensorRT defaults toward GPU export, OpenVINO inference accepts Intel device strings, and CoreML export may use CPU/MPS/GPU depending on platform.
- `half` and `int8`: mutually exclusive in exporter behavior; `int8=True` needs representative calibration data for reliable accuracy.
- `data` and `fraction`: calibration dataset and subset fraction for INT8 formats such as ONNX, OpenVINO, TensorRT, TFLite, Edge TPU, IMX, RKNN, Axelera, DeepX, and QNN.
- `dynamic`, `batch`, `nms`, `opset`, `simplify`, `workspace`, `keras`, and `optimize`: format-specific knobs; verify support before adding them.

See `references/workflows.md` for recipes and `references/api-reference.md` for the format matrix. See `references/troubleshooting.md` when export fails before recommending broad dependency reinstallations.

## Safe Planning Script

Use the bundled script to validate a requested target without running export:

```bash
python sub-skills/export-and-deployment/scripts/plan_export.py --model yolo26n.pt --format onnx --dynamic --int8 --data coco8.yaml
python sub-skills/export-and-deployment/scripts/plan_export.py --model best.pt --format engine --device cpu
```

The script emits JSON with the planned `yolo export` command, supported arguments, dependency extra notes, and warnings such as CPU-only TensorRT or ONNX `export-base` requirements.
