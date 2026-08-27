# Data Formats

## Shapes synthetic dataset

The Shapes sample generates simple circles, squares, and triangles on the fly. It is useful for smoke-testing the data pipeline because it has no external dataset download.

Key config ideas:

- `NUM_CLASSES = 1 + 3` for background plus square/circle/triangle.
- Small images such as `128x128` and anchors `(8, 16, 32, 64, 128)` reduce smoke-test cost.
- The dataset metadata stores shape specs in `image_info`; `load_image()` draws them, and `load_mask()` draws one binary mask per instance while handling occlusion.

Use the bundled `scripts/generate_shapes_fixture.py` for a self-contained fixture; it does not import the original sample.

<a id="balloon--via-polygons"></a>
## Balloon / VIA polygons

The Balloon sample is a one-class training and color-splash workflow. Expected dataset layout:

```text
balloon_dataset/
  train/
    via_region_data.json
    image files...
  val/
    via_region_data.json
    image files...
```

VIA annotation facts:

- VIA 1.x writes `regions` as a dictionary; VIA 2.x may write a list.
- Each polygon region has `shape_attributes` with `all_points_x`, `all_points_y`, and `name: polygon`.
- The loader reads image dimensions from the image file because VIA JSON may not include dimensions.
- `load_mask()` rasterizes polygons into `[height, width, instance_count]` masks and returns class id 1 for every balloon instance.

## COCO

COCO workflows require `pycocotools`. Common layout:

```text
coco_root/
  annotations/
    instances_train2014.json
    instances_val2014.json
    instances_minival2014.json        # optional split
    instances_valminusminival2014.json # optional split
  train2014/
  val2014/
```

For 2017, use `train2017`/`val2017` and matching annotation names. The sample's loader accepts subsets such as `train`, `val`, `minival`, and `valminusminival`, and maps `minival`/`valminusminival` images under `val<year>`.

COCO mask conversion handles polygon, uncompressed RLE, and compressed RLE through pycocotools. Crowd annotations use negative class ids to mark exclusion regions.

## Nucleus / Data Science Bowl

The Nucleus sample expects image ids as directories. Typical layout:

```text
nucleus_root/
  stage1_train/
    <image_id>/
      images/<image_id>.png
      masks/*.png
  stage1_test/
    <image_id>/
      images/<image_id>.png
```

Supported subsets in the sample: `train`, `val`, `stage1_train`, `stage1_test`, and `stage2_test`.

- `train` is `stage1_train` minus a hard-coded validation list.
- `val` is the hard-coded validation list inside `stage1_train`.
- Training masks are read from one PNG per instance under `masks/`.
- Inference/submission output converts predicted instance masks to run-length encoding; route RLE tasks to [inference-evaluation](../../inference-evaluation/SKILL.md).

## Shared mask and bbox conventions

- Mask arrays are height-major: `[H, W, instances]`.
- Bounding boxes use `[y1, x1, y2, x2]`.
- COCO result `bbox` uses `[x, y, width, height]`, so conversion is required.
- Nucleus RLE is column-major after transposing/flattening, not ordinary row-major string encoding.
