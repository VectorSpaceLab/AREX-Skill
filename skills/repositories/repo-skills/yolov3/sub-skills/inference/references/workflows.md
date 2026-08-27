# Inference Workflows

## Deterministic offline probe

From the generated skill directory, point the helper at a YOLOv3 checkout:

```bash
python sub-skills/inference/scripts/yolov3_inference_smoke.py --repo-root <yolov3-checkout> --cfg models/yolov3-tiny.yaml --imgsz 64 --device cpu
```

It builds `models.yolo.Model` from YAML and runs a zero tensor forward. Expected output shape for the default tiny model is `(1, 60, 85)`.

## Native detection command

```bash
python detect.py --weights yolov3-tiny.pt --source data/images --imgsz 640 --device cpu --project runs/detect --name exp --exist-ok
```

Use this command only when official weights and sample images are available or network downloads are approved. Add:

- `--save-txt --save-conf` for YOLO-format text predictions with confidences.
- `--save-crop` for cropped object images.
- `--classes 0 2 3` to filter classes.
- `--conf-thres 0.1` to diagnose empty outputs.
- `--nosave` for prediction-only runs that should not write annotated images.
- `--half` only on compatible CUDA paths; keep CPU runs in FP32.
- `--dnn` when using ONNX with OpenCV DNN instead of the default ONNX runtime path.

## PyTorch Hub custom load

```python
import torch
model = torch.hub.load('.', 'custom', 'runs/train/smoke/weights/best.pt', source='local', device='cpu')
results = model('data/images/bus.jpg', size=320)
results.print()
```

For official pretrained Hub models, expect network access unless weights are cached.

## Output locations

`detect.py` writes to `runs/detect/<name>` by default and auto-increments unless `--exist-ok` is passed. Text labels live under `labels/` when `--save-txt` is enabled.
