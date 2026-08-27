# Ultralytics Data and Configuration Workflows

This reference covers safe data/config work for Ultralytics package version 8.4.72. The installed package exposes console scripts `yolo` and `ultralytics`; the canonical CLI shape is:

```bash
yolo TASK MODE arg=value arg=value
```

`TASK` is optional when Ultralytics can infer it from the model, but include it for clarity when planning. Valid tasks are `detect`, `segment`, `semantic`, `classify`, `pose`, and `obb`. Valid modes are `train`, `val`, `predict`, `track`, `export`, and `benchmark`.

## Dataset YAML Rules

### Detection, Segment, Pose, OBB, and Semantic

Ultralytics detection-like dataset YAMLs are checked by package utilities before training/validation. Required keys:

- `train`: training image directory, image-list text file, or list of either.
- `val`: validation image directory, image-list text file, or list of either. A legacy `validation` key is renamed to `val`, but write `val` directly.
- `names` or `nc`: class names are preferred. If both exist, `len(names)` must equal `nc`.
- `path`: optional dataset root. Relative `train`/`val` values resolve under `path`; when `path` is relative and missing locally, Ultralytics may resolve it under its configured datasets directory.

Recommended detection-like template:

```yaml
path: dataset_root
train: images/train
val: images/val
test:
names:
  0: class_a
  1: class_b
```

Useful task-specific additions:

- `pose`: add `kpt_shape: [num_keypoints, 2_or_3]`; add `flip_idx` for symmetric left/right keypoint swaps; optionally add `kpt_names`.
- `semantic`: add `masks_dir: masks`; for label remapping, add `label_mapping` values where ignored labels map to `ignore_label`.
- `obb`: labels use oriented bounding boxes, but the YAML still follows the same `path`/`train`/`val`/`names` shape.
- `segment`: instance segment labels live in YOLO polygon-label text files; the dataset YAML resembles detection.

`download:` is optional. It can be a URL, a `bash ...` command, or Python code executed with the YAML dictionary in scope when autodownload is enabled. Review it before allowing a command that may autodownload.

### Classification

Classification datasets are directory roots, not dataset YAML files. Expected structure:

```text
dataset_root/
  train/
    class_a/*.jpg
    class_b/*.jpg
  val/
    class_a/*.jpg
    class_b/*.jpg
  test/          # optional
```

If `train/` is missing but images exist in class subdirectories, Ultralytics may try to create a split copy. Plan this as a filesystem-mutating step, not a read-only validation.

## CLI and Python Argument Translation

Python API calls use kwargs:

```python
from ultralytics import YOLO
model = YOLO("yolo26n.pt")
model.train(data="custom.yaml", epochs=10, imgsz=640, device="cpu")
```

Canonical CLI translation:

```bash
yolo detect train model=yolo26n.pt data=custom.yaml epochs=10 imgsz=640 device=cpu
```

Rules:

- Every CLI override after `TASK MODE` must be `arg=value`; do not use `--arg value`.
- Quote values only when the shell needs it, such as paths with spaces, JSON-like lists, URLs containing `&`, or tracker regions.
- Lists can be rendered as compact literals such as `imgsz=640,480`, `classes=[0,2]`, or `device=[0,1]` depending on the target argument.
- `cfg=custom.yaml` loads a config file first; explicitly provided CLI/Python kwargs still override config values.
- Unknown keys cause alignment errors. Current deprecation mappings include `boxes` to `show_boxes`, `hide_labels` to inverted `show_labels`, `hide_conf` to inverted `show_conf`, and `line_thickness` to `line_width`; removed keys include `label_smoothing`, `save_hybrid`, and `crop_fraction`.

## Important Config Keys

Common train/data keys: `model`, `data`, `epochs`, `time`, `patience`, `batch`, `imgsz`, `cache`, `device`, `workers`, `project`, `name`, `exist_ok`, `pretrained`, `optimizer`, `seed`, `deterministic`, `single_cls`, `rect`, `resume`, `amp`, `fraction`, `freeze`, `multi_scale`, `compile`.

Validation/predict keys: `split`, `save_json`, `conf`, `iou`, `max_det`, `half`, `dnn`, `plots`, `source`, `vid_stride`, `stream_buffer`, `visualize`, `augment`, `classes`, `retina_masks`, `embed`.

Visualization/output keys: `show`, `save`, `save_frames`, `save_txt`, `save_conf`, `save_crop`, `show_labels`, `show_conf`, `show_boxes`, `line_width`.

Export keys: `format`, `keras`, `optimize`, `int8`, `dynamic`, `simplify`, `opset`, `workspace`, `nms`, `data`, `fraction`, `device`, `imgsz`, `batch`, `half`.

Augmentation/hyperparameter keys include `lr0`, `lrf`, `momentum`, `weight_decay`, `warmup_epochs`, `box`, `cls`, `dfl`, `pose`, `angle`, `hsv_h`, `hsv_s`, `hsv_v`, `degrees`, `translate`, `scale`, `shear`, `perspective`, `flipud`, `fliplr`, `mosaic`, `mixup`, `cutmix`, `copy_paste`, `auto_augment`, and `erasing`.

## Safe Command Planning Examples

Review a dataset YAML without launching training:

```bash
python sub-skills/data-and-configuration/scripts/validate_dataset_yaml.py custom.yaml --task detect --check-paths
```

Render a train command from kwargs without running it:

```bash
python sub-skills/data-and-configuration/scripts/plan_yolo_command.py \
  --task detect --mode train --model yolo26n.pt \
  --kwargs '{"data":"custom.yaml","epochs":1,"imgsz":320,"device":"cpu","workers":0}'
```

Plan validation after a model exists:

```bash
yolo detect val model=best.pt data=custom.yaml batch=1 imgsz=640 device=cpu
```

Plan export with INT8 calibration data explicitly reviewed:

```bash
yolo export model=best.pt format=onnx int8=True data=custom.yaml imgsz=640 device=cpu
```

## Converters and Split Helpers

Use these Python APIs only after confirming source/output paths because they write files:

```python
from ultralytics.data.converter import convert_coco, convert_dota_to_yolo_obb, convert_segment_masks_to_yolo_seg
from ultralytics.data.split import autosplit, split_classify_dataset

convert_coco(labels_dir="annotations", save_dir="converted", use_segments=False, use_keypoints=False)
convert_coco(labels_dir="annotations", save_dir="converted-seg", use_segments=True)
convert_coco(labels_dir="annotations", save_dir="converted-pose", use_keypoints=True)
convert_dota_to_yolo_obb("DOTA")
convert_segment_masks_to_yolo_seg(masks_dir="masks", output_dir="labels", classes=2)
autosplit(path="images", weights=(0.8, 0.2, 0.0), annotated_only=True)
split_classify_dataset("classification_root", train_ratio=0.8)
```

Network dataset download shell scripts are intentionally not bundled here: they download large datasets and are unsuitable as safe default runtime helpers.
