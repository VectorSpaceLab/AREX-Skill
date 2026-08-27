# YOLOX Model And API Reference

This reference collects model-selection and runtime API facts needed for inference without reopening a source checkout.

## Built-in model selectors

| Name | Depth | Width | Size | Notes |
|---|---:|---:|---:|---|
| `yolox-s` | 0.33 | 0.50 | 640 | Small standard PAFPN/head. |
| `yolox-m` | 0.67 | 0.75 | 640 | Medium model. |
| `yolox-l` | 1.00 | 1.00 | 640 | Large model. |
| `yolox-x` | 1.33 | 1.25 | 640 | Extra-large model. |
| `yolox-tiny` | 0.33 | 0.375 | 416 | Tiny/mobile, mixup disabled. |
| `yolox-nano` | 0.33 | 0.25 | 416 | Nano/mobile, depthwise model, mixup disabled. |
| `yolov3` | 1.00 | 1.00 | 640 | Darknet/YOLOv3-style model path. |

Use larger models for accuracy when compute allows; use tiny/nano for mobile or smoke tests.

## Key API signatures

```python
get_exp(exp_file=None, exp_name=None)
YOLOX(backbone=None, head=None)
YOLOPAFPN(depth=1.0, width=1.0, in_features=("dark3", "dark4", "dark5"), in_channels=[256, 512, 1024], depthwise=False, act="silu")
YOLOXHead(num_classes, width=1.0, strides=[8, 16, 32], in_channels=[256, 512, 1024], act="silu", depthwise=False)
ValTransform(swap=(2, 0, 1), legacy=False)
postprocess(prediction, num_classes, conf_thre=0.7, nms_thre=0.45, class_agnostic=False)
vis(img, boxes, scores, cls_ids, conf=0.5, class_names=None)
fuse_model(model)
get_model_info(model, tsize)
```

`get_exp` uses `exp_file` when provided; otherwise it converts names such as `yolox-s` to default experiment modules.

## Checkpoint expectations

YOLOX training checkpoints usually store weights under `ckpt["model"]`. Export or externally saved files may be raw state dicts. For inference, match:

- model selector (`--name` or `--exp-file`),
- `num_classes`,
- depth/width/depthwise settings,
- preprocessing legacy setting,
- and checkpoint source.

Head shape mismatches almost always mean the checkpoint and `Exp` were not produced for the same class count or architecture.

## Source script treatment

- The demo script was adapted into command/API recipes and `../scripts/yolox_inference_smoke.py`; it was not copied because real demos require user checkpoints, input media, and may open GUI/video devices or write outputs.
- Training/evaluation scripts are owned by `../training-and-data/SKILL.md`.
- Export/TensorRT scripts are owned by `../export-and-deployment/SKILL.md`.
- Assignment visualization is a training/debug route, not an inference route.
