# Data tools and recipes

Use this reference after checking the dataset format. The bundled scripts cover deterministic validation and a compact YOLO-to-COCO conversion path. Heavier MMYOLO utilities are distilled as option maps and safety recipes because they build datasets, open visualizers, copy files, run clustering, or require optional dependencies.

## Recommended data-prep sequence

1. Normalize labels into COCO detection JSON or a supported MMYOLO dataset format.
2. Validate the JSON with `scripts/inspect_coco_annotations.py`.
3. Check class ordering against `metainfo.classes` and the model head class count.
4. For anchor-based models, optimize anchors after the training dataset config builds successfully.
5. Browse a small visual sample before spending training time.
6. Only then route actual training or evaluation to the training-evaluation workflow.

## Bundled helper: inspect COCO annotations

Run:

```bash
python scripts/inspect_coco_annotations.py annotations/trainval.json --image-root images --require-annotations
```

Useful flags:

- `--image-root DIR`: check that every `images[*].file_name` resolves under an image directory.
- `--require-annotations`: fail if the file has no annotations; useful for train/val splits.
- `--allow-out-of-bounds`: downgrade boxes extending outside image bounds from errors to warnings.
- `--strict-area`: fail when `area` is missing or inconsistent with bbox area.
- `--strict-warnings`: return non-zero on warnings as well as errors.
- `--json`: emit a machine-readable summary for automation.

This script is adapted from MMYOLO's COCO browsing use case but removes UI, image loading, plotting, pycocotools, and MMYOLO dependencies. It is appropriate for pre-training CI and tiny fixtures.

## Bundled helper: YOLO txt to COCO skeleton

Run on a YOLO root containing `classes.txt`, `images/`, and `labels/`:

```bash
python scripts/convert_yolo_txt_to_coco_skeleton.py YOLO_ROOT --out annotations/result.json
```

If image dimensions cannot be read from files in the current environment, provide a fixed size for a tiny fixture or uniform dataset:

```bash
python scripts/convert_yolo_txt_to_coco_skeleton.py YOLO_ROOT \
  --out annotations/result.json \
  --image-width 640 --image-height 480
```

Useful flags:

- `--category-id-start 0|1`: choose whether COCO category ids mirror YOLO zero-based class ids or start at one.
- `--list-file FILE`: convert only images named by a split file. Absolute entries are matched by basename for compatibility with YOLO split lists.
- `--allow-missing-labels`: keep images with no label txt as negative images.
- `--allow-empty`: permit an output with zero annotations.
- `--indent N`: control JSON formatting.

The converter fails on malformed rows, class ids outside `classes.txt`, normalized values outside `[0, 1]`, zero/negative box sizes, and boxes whose derived corners leave the image. Validate its output with `inspect_coco_annotations.py` before config integration.

## Browsing COCO annotations

Use this when the user needs to visually confirm that converted boxes align with images. The maintained MMYOLO browser accepts these concepts:

- Data root plus relative image directory and annotation file, or direct image directory plus direct annotation file.
- Optional category-name filter, e.g. only `cat` and `dog`.
- Display bbox-only by default, or all annotation types when masks are needed.
- Optional shuffle and wait time for interactive review.

This skill bundles a non-visual validator instead of the visual browser because the original workflow requires OpenCV, matplotlib, pycocotools, a display or output backend, and image files. For unattended checks, prefer `inspect_coco_annotations.py`; for human review, sample a small subset and keep the visual side effects explicit.

## Browsing built datasets and pipelines

Dataset browsing answers: "does the MMYOLO config build the intended dataset and do transforms look sane?" The maintained browser operates from a config and supports:

- `phase`: `train`, `val`, or `test` dataset.
- `mode`: original image, transformed image, or intermediate pipeline comparison.
- Output directory for saved visualizations.
- Headless mode (`not-show`) and image count/interval controls.
- Config overrides in `key=value` form for quick `data_root` or dataloader fixes.

Reference-only reason: this builds the configured dataset, executes transforms, writes images, and may require GUI/visualization dependencies. Use after schema validation and before training, not as the first data check.

## Dataset statistics

Dataset analysis summarizes class balance and bbox geometry. The maintained statistics workflow produces:

- Category and bbox-instance distribution.
- Bbox width/height distribution.
- Bbox aspect-ratio distribution.
- Bbox area distribution according to configurable area thresholds.
- Class/data-list printouts.

Core option concepts:

- Config file: source of the dataset definition.
- Train dataset by default; switch to validation when needed.
- `class_name`: focus one class.
- `area_rule`: up to three custom thresholds, interpreted with lower/upper sentinel bounds.
- `func`: run one plot type instead of all.
- `out_dir`: folder for generated figures.

Reference-only reason: it performs plotting and reads the dataset through MMYOLO/MMEngine. Run it on a small prepared dataset and keep generated figures outside the runtime skill tree.

## Anchor optimization

Anchor optimization is only relevant for anchor-based YOLO heads such as YOLOv5-style configs. Skip it for anchor-free models such as YOLOX, YOLOv6-style, YOLOv8 point-generator heads, and RTMDet unless the active config explicitly uses anchor base sizes.

Supported algorithm concepts:

- `k-means`: IoU-based clustering.
- `DE`: differential evolution on average IoU cost.
- `v5-k-means`: YOLOv5-style shape-match clustering; commonly uses `prior_match_thr=4.0`.

Checklist:

1. Build a correct training dataset config first.
2. Use `input_shape` as `[width height]`, usually the train image scale.
3. Set device intentionally; some defaults prefer CUDA, but CPU may be acceptable for small datasets.
4. Expect randomness from clustering initialization.
5. Copy the resulting anchors into the config's `prior_generator.base_sizes` for anchor-based heads.
6. Re-run a config summary/parse check after editing anchors.

Reference-only reason: it builds the dataset, runs numerical optimization, can be slow on large datasets, writes outputs, and depends on optional scientific plotting/optimization packages.

## COCO subsets and splits

Use subset/split utilities for debugging or custom-dataset partitioning after the source COCO JSON is valid.

### Extracting a COCO subset

The COCO subset workflow targets COCO2017-style roots with `annotations/`, `train2017/`, `val2017/`, and `test2017/`. It can filter by:

- Number of images (`num_img`, where `-1` means all after filtering).
- Classes.
- COCO area size (`small`, `medium`, `large`).
- Whether the training subset is drawn from the real training set rather than validation.
- Seed for reproducibility.

Reference-only reason: it copies image files and writes new annotations. Use an explicit output directory and keep the original data immutable.

### Splitting one COCO JSON

The COCO split workflow divides one JSON into train/val/test-style JSON files with:

- `ratios`: two numbers for `trainval + test`, or three for `train + val + test`; integer ratios are normalized like decimal ratios.
- Optional shuffle.
- Optional seed.

After splitting, inspect every output JSON and update `train_dataloader`, `val_dataloader`, `test_dataloader`, and evaluator `ann_file` together.

## DOTA split recipe

DOTA images are usually too large for direct rotated-detection training. The DOTA split workflow takes:

- A split config such as single-scale or multi-scale patch settings.
- Raw DOTA root.
- Output directory.
- Annotation subdirectory such as `labelTxt-v1.0` or `labelTxt-v1.5`.
- Phases: `trainval`, `train`, `val`, and/or `test`.
- Process count, output image extension, and overwrite control.

Safety and dependency notes:

- Requires image slicing dependencies such as `shapely`; rotated dataset loading also requires the rotated-detection package stack.
- Outputs a new split root with `images/` and `annfiles/` per phase.
- After splitting, set rotated configs' `data_root` to the split output.
- Do not overwrite a previous split unless the user explicitly wants replacement.

## Downloaders are network references only

MMYOLO documents downloader support for datasets such as COCO2017, VOC2007, VOC2012, LVIS, cat, and balloon. Treat downloader commands as network references only. Before running one, confirm dataset name, output directory, unzip/delete behavior, and expected size. Do not put downloaded archives or extracted datasets inside the skill tree.

## Dataset classes and transform API facts

Installed/source evidence shows these MMYOLO dataset wrappers:

| Name | Role |
| --- | --- |
| `YOLOv5CocoDataset` | COCO detection wrapper with batch-shape policy and Mosaic/MixUp dataset injection during training. |
| `YOLOv5VOCDataset` | VOC wrapper with the same batch-shape policy support. |
| `YOLOv5DOTADataset` | DOTA rotated-detection wrapper; raises an import error when rotated-detection dependencies are unavailable. |
| `YOLOv5CrowdHumanDataset` | CrowdHuman wrapper for ODGT-style crowd-human configs. |
| `PoseCocoDataset` | MMPose COCO wrapper used by pose-related examples. |
| `BatchShapePolicy` / `yolov5_collate` | Utility surfaces used by batching and dataloaders. |

Key transform signatures to recognize in configs:

| Transform | Signature summary | Notes |
| --- | --- | --- |
| `YOLOv5KeepRatioResize` | `scale`, `keep_ratio=True`, `**kwargs` | Tests assert keep-ratio behavior and scale-factor correctness. |
| `LetterResize` | `scale`, `pad_val`, `use_mini_pad`, `stretch_only`, `allow_scale_up`, `half_pad_param`, `**kwargs` | Produces `pad_param` and handles stride-friendly padding. |
| `LoadAnnotations` | `mask2bbox=False`, `poly2mask=False`, `merge_polygons=True`, `**kwargs` | MMYOLO variant adapts YOLO ignore/mask handling. |
| `YOLOv5RandomAffine` | rotation/translate/scale/shear/border/filter thresholds | Can drop tiny boxes via `min_bbox_size`, `min_area_ratio`, and `max_aspect_ratio`. |
| `Mosaic` | `img_scale`, `center_ratio_range`, `bbox_clip_border`, `pad_val`, `pre_transform`, `prob`, cache controls | Requires dataset access injected during training. |
| `Mosaic9` | `img_scale`, `bbox_clip_border`, `pad_val`, `pre_transform`, `prob`, cache controls | Nine-image variant; cache size assertions are test-backed. |
| `YOLOv5MixUp` | `alpha`, `beta`, `pre_transform`, `prob`, cache controls | MixUp augmentation for YOLOv5-style pipelines. |
| `YOLOXMixUp` | YOLOX-style MixUp with image-scale behavior | Used in YOLOX-like pipelines. |

For API-level module extension or registry details, route to `model-api`; for deciding which transforms belong in a config, route to `config-customization` after validating the dataset.

## Source-script bundling decisions

| Capability | Bundled here? | Reason |
| --- | --- | --- |
| COCO annotation inspection | Yes: `scripts/inspect_coco_annotations.py` | Deterministic validation can be made self-contained without visualization dependencies. |
| YOLO txt conversion | Yes: `scripts/convert_yolo_txt_to_coco_skeleton.py` | Common small conversion path; normalized-coordinate validation is valuable before training. |
| Visual COCO browsing | No, recipe only | Requires image display/plotting and optional COCO visualization dependencies. |
| Dataset pipeline browsing | No, recipe only | Builds datasets and runs transforms; visual side effects are not safe as a bundled helper. |
| Dataset statistics | No, recipe only | Plotting and full-dataset traversal can be slow and writes outputs. |
| Anchor optimization | No, recipe only | Potentially long-running optimization with optional scientific dependencies. |
| LabelMe/balloon converters | No, recipe only | Full conversion logic is larger and dataset-specific; use COCO validator after conversion. |
| Downloaders | No, network reference only | Downloads, extracts, and optionally deletes archives. |
| COCO subset/split tools | No, recipe only | Copy/write data outputs; safer as an explicit user-approved operation. |
| DOTA split | No, recipe only | Large data mutation plus optional rotated-detection/image-slicing dependencies. |
