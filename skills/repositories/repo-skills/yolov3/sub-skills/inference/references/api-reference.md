# YOLOv3 Inference API Reference

## PyTorch Hub

`hubconf.py` exposes:

- `yolov3(pretrained=True, channels=3, classes=80, autoshape=True, _verbose=True, device=None)`
- `yolov3_spp(pretrained=True, channels=3, classes=80, autoshape=True, _verbose=True, device=None)`
- `yolov3_tiny(pretrained=True, channels=3, classes=80, autoshape=True, _verbose=True, device=None)`
- `custom(path="path/to/model.pt", autoshape=True, _verbose=True, device=None)`

Examples:

```python
import torch
model = torch.hub.load('ultralytics/yolov3', 'yolov3_tiny', device='cpu')
model = torch.hub.load('.', 'custom', 'runs/train/smoke/weights/best.pt', source='local', device='cpu')
```

Offline model-construction smoke from the generated skill directory, pointing at a YOLOv3 checkout:

```bash
python sub-skills/inference/scripts/yolov3_hub_smoke.py --repo-root <yolov3-checkout> --model yolov3-tiny --no-pretrained --no-forward
```

The helper accepts `--pretrained`, `--no-pretrained`, and `--no-forward`.

## Native detect CLI

`detect.py` key arguments:

- `--weights`: one or more checkpoint/model paths or Triton URL; default is `yolov3-tiny.pt`.
- `--source`: file, directory, URL, glob, webcam index, screen, or stream source; default is `data/images`.
- `--data`: dataset YAML, default `data/coco128.yaml`, used for class names.
- `--imgsz` / `--img` / `--img-size`: one or two image sizes.
- `--conf-thres`, `--iou-thres`, `--max-det`: filtering and NMS.
- `--device`: `cpu`, a CUDA id, or comma-separated CUDA ids.
- `--save-txt`, `--save-conf`, `--save-crop`, `--nosave`: output controls.
- `--classes`, `--agnostic-nms`, `--augment`, `--visualize`, `--half`, `--dnn`, `--vid-stride`.
- `--project`, `--name`, `--exist-ok`: output directory control.

## DetectMultiBackend

`models/common.py:DetectMultiBackend` handles `.pt`, TorchScript, ONNX, OpenVINO, TensorRT engine, CoreML, TensorFlow-family suffixes for externally produced models, Paddle, Triton, and TFLite/EdgeTPU. Match export format and runtime dependencies before choosing `--dnn`, `--half`, or accelerator-specific files.
