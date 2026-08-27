# YOLOP Data Layout and Label Formats

## When to read

Read this when wiring BDD100K data into YOLOP, generating drivable-area masks, checking whether detection JSONs match images, or debugging `BddDataset` path assumptions.

## README layout

The README recommends a combined dataset root with these subdirectories:

```text
dataset-root/
  images/
    train/
    val/
  det_annotations/
    train/
    val/
  da_seg_annotations/
    train/
    val/
  ll_seg_annotations/
    train/
    val/
```

The source config instead stores four independent roots in `cfg.DATASET`:

```python
DATASET.DATAROOT   # images root, containing train/ and val/
DATASET.LABELROOT  # detection JSON root, containing train/ and val/
DATASET.MASKROOT   # drivable-area mask root, containing train/ and val/
DATASET.LANEROOT   # lane-line mask root, containing train/ and val/
```

When using the README combined layout, map those config fields to `dataset-root/images`, `dataset-root/det_annotations`, `dataset-root/da_seg_annotations`, and `dataset-root/ll_seg_annotations`.

## How `BddDataset` pairs files

`BddDataset` iterates over drivable-area mask files first. For every mask file under `MASKROOT/<split>`, it derives the other paths by replacing roots and extensions:

```text
mask:  MASKROOT/<split>/<stem>.png
label: LABELROOT/<split>/<stem>.json
image: DATAROOT/<split>/<stem>.jpg
lane:  LANEROOT/<split>/<stem>.png
```

This means a missing drivable mask can silently remove an otherwise valid image from the dataset, and a mismatched mask stem causes label/image/lane lookup failures.

## Detection JSON schema used by source

`lib/dataset/bdd.py` opens each detection JSON and reads:

```python
label["frames"][0]["objects"]
```

For each object with `box2d`, it uses:

```text
object.category
object.box2d.x1, y1, x2, y2
object.attributes.trafficLightColor  # only when category == "traffic light"
```

The active source sets `single_cls = True`, so only vehicle-like categories from `id_dict_single` remain and all selected classes become class id 0:

```text
car, bus, truck, train -> 0
```

If `single_cls` is changed to `False`, the larger `id_dict` maps person/rider/car/bus/truck/bike/motor/traffic-light colors/sign/train into multi-class labels.

Coordinates are converted to normalized YOLO `(center_x, center_y, width, height)` using image size from `cfg.DATASET.ORG_IMG_SIZE` (default `[720, 1280]`, interpreted in source as height/width).

## Drivable-area mask generation

The source `toolkits/datasetpre/gen_bdd_seglabel.py` rasterizes BDD polygon annotations:

- Categories starting with `area` are considered.
- `area/drivable` polygons become white/foreground.
- `area/alternative` and non-drivable area categories remain black/background in the source behavior.
- Output PNGs are named from the BDD label's `name` field plus `.png`.

Use the bundled `generate_drivable_masks.py` helper for an argument-driven version. It is designed for explicit `--labels-dir` and `--output-dir` rather than the source script's hard-coded `bdd/...` paths.

## Training/evaluation image preprocessing

`AutoDriveDataset.__getitem__`:

1. Reads the RGB image, drivable mask, and lane mask.
2. Resizes to keep the longest side at `MODEL.IMAGE_SIZE`.
3. Applies YOLO-style letterbox padding to a stride-compatible shape.
4. Converts detection boxes from normalized xywh to padded pixel xyxy, applies training augmentation, then converts back to normalized xywh.
5. Converts drivable and lane masks to two-channel tensors: background and foreground.
6. Returns `(img, [det_labels, da_seg_label, lane_label], image_path, shapes)`.

For evaluation, `shapes` preserves the original image size and padding/ratio so detections and masks can be scaled back.

## Validation checklist

Before training/evaluation:

- Each root contains the requested split names (`train`, `val` by default).
- Drivable mask stems, lane mask stems, detection JSON stems, and image stems correspond.
- Images are `.jpg`; masks are `.png`; detection labels are `.json`.
- Detection JSON has `frames[0].objects` and object `box2d` values.
- `cfg.DATASET.ORG_IMG_SIZE` matches the raw image coordinate frame used by annotations.
- For small experiments, reduce `WORKERS`, `TRAIN.BATCH_SIZE_PER_GPU`, and `TEST.BATCH_SIZE_PER_GPU` because defaults assume a larger GPU workflow.
