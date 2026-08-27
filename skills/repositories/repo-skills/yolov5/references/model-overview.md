# Model and API Overview

## Task families

YOLOv5 exposes three main task families in this checkout:

| Task | Entrypoints | Model/checkpoint family | Main output |
| --- | --- | --- | --- |
| Object detection | detection train/val/inference and PyTorch Hub | `yolov5n/s/m/l/x`, P6 variants, custom detection checkpoints | boxes, confidence, class ids/names |
| Instance segmentation | segmentation train/val/predict | `yolov5*-seg.pt`, `models/segment/*.yaml` | boxes plus masks |
| Image classification | classification train/val/predict | `yolov5*-cls.pt`, torchvision model names | class probabilities/top-k predictions |

Route export and benchmark tasks to `sub-skills/export/` after selecting a task-compatible checkpoint.

## Inspected public signatures

These signatures were verified during skill construction. Default path values are normalized here; actual defaults may resolve relative to a working checkout.

```python
hubconf.custom(path="path/to/model.pt", autoshape=True, _verbose=True, device=None)
hubconf.yolov5s(pretrained=True, channels=3, classes=80, autoshape=True, _verbose=True, device=None)
hubconf._create(name, pretrained=True, channels=3, classes=80, autoshape=True, verbose=True, device=None)
models.common.DetectMultiBackend(weights="yolov5s.pt", device="cpu", dnn=False, data=None, fp16=False, fuse=True)
models.common.AutoShape(model, verbose=True)
models.yolo.DetectionModel(cfg="yolov5s.yaml", ch=3, nc=None, anchors=None)
models.yolo.SegmentationModel(cfg="yolov5s-seg.yaml", ch=3, nc=None, anchors=None)
models.yolo.ClassificationModel(cfg=None, model=None, nc=1000, cutoff=10)
utils.triton.TritonRemoteModel(url: str)
```

## PyTorch Hub behavior

PyTorch Hub functions in `hubconf.py` support official model names and custom checkpoints. Key choices:

- `pretrained=True` downloads official weights for standard models when needed.
- `custom(path, autoshape=True, device=None)` loads a local or downloaded checkpoint.
- `autoshape=True` wraps detection models so they accept file paths, URLs, PIL images, OpenCV/numpy arrays, and lists; classification and segmentation models have limitations in this wrapper path.
- `device` may be `cpu`, `cuda`, `cuda:0`, or a torch device; use explicit devices for deterministic behavior.
- Cache errors may need a forced Hub reload, but avoid network/cache mutation unless the task authorizes it.

## DetectMultiBackend and export formats

`DetectMultiBackend` is the central inference wrapper for multiple formats. It supports PyTorch checkpoints plus exported formats such as TorchScript, ONNX, OpenVINO, TensorRT engines, CoreML, TensorFlow SavedModel/GraphDef/TFLite/EdgeTPU/TF.js, and Paddle where dependencies are installed.

Use `sub-skills/export/references/formats.md` before relying on non-PyTorch formats. Exported files often have runtime-specific constraints:

- TensorRT engines are tied to the TensorRT version, GPU architecture, and runtime environment.
- CoreML validation is platform-sensitive.
- ONNX export is the lightest common non-PyTorch path but still requires `onnx`.
- TFLite/TF.js/Paddle/OpenVINO require their own package stacks.

## Model YAMLs

- `models/yolov5n.yaml` through `models/yolov5x.yaml`: standard P5 detection architectures.
- `models/hub/yolov5*6.yaml`: P6 high-resolution variants.
- `models/hub/`: experimental/backbone/FPN/PANet/Ghost/Transformer variants; use only when the task explicitly asks for them.
- `models/segment/yolov5*-seg.yaml`: segmentation architectures.

When training from scratch, pair the task script with a compatible YAML and data config. When fine-tuning, pair the task script with a compatible checkpoint family.

## Choosing a model family

- Use `yolov5n` or `yolov5s` for fast smoke checks, CI-style local validation, and CPU-friendly tests.
- Use larger P5 models for accuracy when compute permits.
- Use P6 models for larger images or high-resolution detection workflows.
- Use `*-seg` only for instance segmentation.
- Use `*-cls` or torchvision model names only for classification.
- Prefer explicit local checkpoint paths when offline, reproducing results, or avoiding automatic downloads.
