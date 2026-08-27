# Data troubleshooting

Use this guide when GluonCV dataset construction, transforms, loaders, metrics, or visual checks fail. Start with data existence and label format before debugging models.

## Missing dataset roots or split files

Symptoms:

- `FileNotFoundError` or `IOError` when constructing `VOCDetection`, `COCODetection`, `ImageNet`, video datasets, or segmentation datasets.
- Dataset length is zero.
- A video dataset cannot open its `setting` file.

Checks and fixes:

1. Print the explicit `root` and `split`/`setting` arguments you are passing; do not assume the default `~/.mxnet/datasets/...` location.
2. Confirm the required subfolders exist:
   - VOC detection: `VOCxxxx/Annotations`, `VOCxxxx/JPEGImages`, `VOCxxxx/ImageSets/Main/<split>.txt`.
   - VOC segmentation: `VOC2012/ImageSets/Segmentation/<split>.txt`, `JPEGImages`, `SegmentationClass`.
   - COCO: `train2017`, `val2017`, `annotations/instances_*.json` or `person_keypoints_*.json`.
   - ADE20K: `ADEChallengeData2016/images/{training,validation}` and `annotations/{training,validation}`.
   - Cityscapes: `leftImg8bit/<split>` and `gtFine/<split>`.
   - Video datasets: decoded frame root plus setting/list file with relative video/frame entries.
3. If using dataset preparation helpers, treat `--no-download` as a promise that all archives or extracted folders already exist. Use `--overwrite` only for replacing corrupted downloads.
4. Keep one small sample image and annotation aside for single-sample validation before using multi-worker loaders.

## Bounding-box coordinate/order errors

Symptoms:

- Assertions such as `xmin must in [0, width)`, `xmax must in (xmin, width]`, or empty labels after parsing.
- Visualized boxes are mirrored, shifted, tiny, or outside the image.
- Detection transforms raise shape/target-generation errors.

Checks and fixes:

1. GluonCV detection boxes are `[xmin, ymin, xmax, ymax, class_id]` after loading. COCO JSON stores `[x, y, width, height]`; GluonCV converts it internally. Do not pass raw COCO width/height boxes directly to bbox transforms.
2. Bbox transform `size` arguments are `(width, height)`, not HWC image shape order.
3. Run the bundled JSON validator for simple custom records:

   ```bash
   python sub-skills/data-transforms-datasets/scripts/validate_detection_record.py records.json --image-root /data/custom --check-files
   ```

4. For normalized LST/RecordIO labels, set `coord_normalized=True`; for already absolute labels, set it to `False`.
5. For VOC XML, remember GluonCV subtracts 1 from the XML box coordinates, then validates zero-based pixel coordinates.
6. After image random crop/expand/flip/resize, apply the matching bbox/mask/pose transform. Image-only geometric transforms invalidate labels.

## Empty or incompatible class lists

Symptoms:

- `ValueError: Incompatible category names with COCO`.
- Custom VOC classes load but model heads do not align.
- All labels are filtered out.

Checks and fixes:

1. COCO dataset class lists must exactly match the annotation category names in COCO order. For custom COCO-style data, subclass and override `CLASSES` only if the JSON categories match that order.
2. VOC class names should be lowercase and stable. Whitespace is stripped with warnings; uppercase class names can fail validation.
3. `skip_empty=True` removes images with no valid objects. Use `skip_empty=False` only when the downstream code can handle dummy invalid labels.
4. When changing model classes, route to `../mxnet-model-zoo/` for reset/reuse-weight guidance.

## `pycocotools`, COCO API, or JSON problems

Symptoms:

- Import errors for `pycocotools`.
- COCO annotation file loads but images are reported missing.
- COCO metrics cannot create result JSON.

Checks and fixes:

1. Install `pycocotools` only for COCO datasets/metrics; it is not required for VOC or simple LST validation.
2. Verify annotation file names: GluonCV expects split strings such as `instances_val2017` and appends `.json` under `annotations/`.
3. COCO image paths are derived from each image entry's URL/name and joined under `root/train2017` or `root/val2017`; custom JSON may require subclassing path parsing.
4. For COCO metrics, pass the same dataset object used for loading and ensure prediction category ids map back to COCO json ids.

## OpenCV, Pillow, and image decode failures

Symptoms:

- `mx.image.imread` fails on a path that exists.
- Resize/affine transforms complain about missing OpenCV.
- Matplotlib/OpenCV visualization fails in a headless environment.

Checks and fixes:

1. Confirm image extensions and actual file bytes match; broken partial downloads often look like image files but cannot decode.
2. Install OpenCV only when needed for resize/affine/video utilities. Some MXNet image routines also rely on OpenCV support.
3. Use a non-interactive Matplotlib backend or OpenCV plotting helpers on servers without displays.
4. For legacy GluonCV stacks that also import Torch submodules, older Pillow may be required; root install guidance covers backend compatibility.

## DataLoader and multiprocessing failures

Symptoms:

- A dataset works for one item but crashes with `num_workers > 0`.
- Worker processes hang or hide the original parsing error.
- Shared-memory or pickling errors.

Checks and fixes:

1. Reproduce with `num_workers=0` and `batch_size=1` first.
2. Validate `__getitem__` for a few sample indices before using random shuffling.
3. Use `Stack` only for same-shape fields. Use `Pad` for variable object counts and `Append` for ragged R-CNN outputs.
4. If a transform function closes over unpicklable state, avoid multiprocessing or move state creation inside the transform class.
5. Large images plus many workers can exhaust shared memory; reduce batch size, workers, or prefetch.

## Video frame extraction and list-building problems

Symptoms:

- UCF101/HMDB51/Kinetics/Something-Something-V2 loaders cannot find frames.
- Output tensor shapes are unexpected.
- Frame extraction commands are slow or fail due to missing codecs.

Checks and fixes:

1. Decide frame-folder mode versus direct video mode. Frame-folder mode needs decoded frames and a setting/list file; direct video mode needs video files and optional `decord`.
2. Match `name_pattern` to actual frame names, e.g. `img_%05d.jpg` versus `%06d.jpg`.
3. Verify `new_length`, `new_step`, `num_segments`, `num_crop`, `slowfast`, and `data_aug` because they change sample shape and temporal selection.
4. Frame extraction and optical-flow options can require `ffmpeg`, `decord`, dense-flow tools, large storage, and long runtime. Plan these as approved side-effectful steps, not ordinary validation.

## RecordIO/LST problems

Symptoms:

- `RecordFileDetection` raises label width/header errors.
- Labels load but boxes are nonsense.
- `.idx` file is missing.

Checks and fixes:

1. Detection RecordIO requires both `.rec` and `.idx` generated with labels packed.
2. LST rows must be tab-separated and include an index, label block, and relative path.
3. The label block's header width must be at least 5; after the header, its length must be divisible by the per-object label width.
4. Choose `coord_normalized` according to how boxes are stored. If normalized but loaded as absolute, boxes collapse near the origin; if absolute but loaded as normalized, boxes become enormous.

## Network and storage constraints

Symptoms:

- Dataset helper downloads fail, partially extracted folders exist, or the user cannot use public mirrors.
- Training examples fail because data is absent even though imports work.

Checks and fixes:

1. Ask before running helper scripts that download/extract tens or hundreds of GB.
2. Use `--download-dir` to point at already-downloaded archives; use `--no-download` only when the helper supports it and the data is complete.
3. Use `--overwrite` for suspected corrupt archives, but warn that it may replace large files.
4. For no-network environments, document the expected layout and build only local validation scripts/lists.

## When to route elsewhere

- The dataset and transform are valid, but the user needs a detector/model object or anchors: route to `../mxnet-model-zoo/`.
- The data layout is for Torch action-recognition configs or DirectPose: route to `../torch-video-workflows/`.
- The user needs an end-to-end train/eval/demo command: route to `../training-evaluation-scripts/`.
- The user wants AutoGluon data wrappers or deployment/export: route to `../automl-deployment-export/`.
