# Detection API Reference

## Verified objects

### `hubconf.custom(path='path/to/model.pt', autoshape=True, _verbose=True, device=None)`

Loads a custom or local YOLOv5 checkpoint.

- `path`: checkpoint path or checkpoint name.
- `autoshape`: wraps the model so it accepts multiple input types and applies NMS.
- `_verbose`: controls Hub load logging.
- `device`: explicit device string or torch device.

### `hubconf.yolov5s(pretrained=True, channels=3, classes=80, autoshape=True, _verbose=True, device=None)`

Creates the standard small detection model.

- `pretrained=True` loads official weights.
- `channels` and `classes` customize non-standard model heads.
- `autoshape` is convenient for common inference input types.

### `models.common.DetectMultiBackend(weights='yolov5s.pt', device='cpu', dnn=False, data=None, fp16=False, fuse=True)`

Common inference wrapper for PyTorch and exported formats.

- `weights`: checkpoint or exported artifact path.
- `dnn=True` uses OpenCV DNN for some ONNX/OpenCV paths.
- `fp16=True` requires compatible CUDA paths.
- `fuse=True` requests layer fusion where supported.

### `models.common.AutoShape(model, verbose=True)`

Wraps a detection model for file/URI/PIL/cv2/numpy inputs and post-NMS output handling.

### `models.yolo.DetectionModel(cfg='yolov5s.yaml', ch=3, nc=None, anchors=None)`

Builds a detection model from a YAML config.

- `cfg`: model YAML file.
- `ch`: input channels.
- `nc`: number of classes.
- `anchors`: anchor settings when relevant.

## Detect CLI parser facts

`detect.py` exposes the source, weights, image size, confidence, IoU, device, save, crop, CSV, class-filter, agnostic-NMS, augmentation, project, run-name, and half/DNN flags needed for routine detection tasks. Use the workflow reference for command shapes; keep this file as the compact API/signal summary.

## Train/val API facts

The inspected module-level helpers expose these signatures:

```python
train.run(**kwargs)
train.parse_opt(known=False)
val.run(data, weights=None, batch_size=32, imgsz=640, conf_thres=0.001, iou_thres=0.6, max_det=300, task='val', device='', workers=8, single_cls=False, augment=False, verbose=False, save_txt=False, save_hybrid=False, save_conf=False, save_json=False, project=..., name='exp', exist_ok=False, half=True, dnn=False, model=None, dataloader=None, save_dir=..., plots=True, callbacks=None, compute_loss=None)
val.parse_opt()
```

Use these signatures to translate between Python and CLI workflows in user-facing answers. Do not quote private output paths from the inspected environment; the default `project` paths in the source are only evidence that the script writes to a run directory.

## Classification and segmentation boundary

`hubconf.py` warns that classification and segmentation models are not fully AutoShape-compatible in the same way as detection models. Route those tasks to the corresponding sub-skill for task-specific loaders and output semantics.
