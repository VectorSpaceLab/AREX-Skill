# Model Architecture Reference

## Built-in YAMLs

- `models/yolov3.yaml`: full YOLOv3 detection model.
- `models/yolov3-spp.yaml`: YOLOv3 with SPP block.
- `models/yolov3-tiny.yaml`: small/tiny model used for CPU smokes.

YAMLs declare `nc`, `depth_multiple`, `width_multiple`, anchors, `backbone`, and `head`. `models/yolo.py:parse_model()` instantiates modules from this declarative structure.

## Main classes

- `models.yolo.Detect`: detection head. It computes `no = nc + 5`, `nl = number of detection layers`, `na = anchors per layer`, registers anchors and anchor grids, and handles train/inference reshaping.
- `models.yolo.BaseModel`: shared forward, fuse, info, and NMS helpers.
- `models.yolo.DetectionModel` / `Model`: build detection models from YAML and calculate strides/anchors.
- `models.common.DetectMultiBackend`: inference wrapper for multiple exported formats.

## Shape sanity

For the default tiny YAML with 80 classes and image size 64:

```bash
python sub-skills/model-architecture/scripts/yolov3_model_yaml_probe.py --repo-root <yolov3-checkout> --cfg models/yolov3-tiny.yaml --imgsz 64 --device cpu
```

Expected prediction shape is `(1, 60, 85)`. The final dimension is 85 because each prediction contains four box values, objectness, and 80 class scores.

## Editing guidance

- Change `nc` and `names` consistently with dataset YAML and checkpoints.
- Changing anchors or heads can invalidate pretrained weights; expect partial weight loading or retraining.
- Preserve detection-only assumptions unless the repository intentionally adds a new task family.
- Prefer modifying existing owner code (`Detect`, `parse_model`, YAML) over adding parallel architecture abstractions.
