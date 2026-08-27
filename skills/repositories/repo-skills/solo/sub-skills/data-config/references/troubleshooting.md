# Data/config troubleshooting

Classify the first failing layer before changing anything: installation/import,
optional transform, schema/path validation, config construction, API/CLI use,
or the training/evaluation workflow. Preserve the original error and the
validated effective config in the handoff.

## Install and import failures

**`No module named mmcv`, `torch`, or `pycocotools`**

- Confirm the process is using the intended environment, then check the
  source-era compatibility target: PyTorch 1.1 or newer, CUDA 9 or newer for
  the intended GPU runtime, and `mmcv==0.2.16`.
- COCO readers import the COCO API at dataset-module import time. A stdlib
  manifest pass can succeed while native COCO construction still fails.
- Do not “fix” an import by mixing a modern MMCV/MMDetection API with this
  v1-era config without recording that compatibility change.

**`undefined symbol`, C++/CUDA import errors, or operator mismatch**

- Treat this as an environment/backend problem, not a bad JSON/XML file.
- Check the installed torch/CUDA/MMCV build pair and whether the extension was
  rebuilt after code or version changes. A CPU check does not validate custom
  CUDA kernels, CUDA NMS, or distributed execution.
- Stop before changing dataset labels; collect versions and the exact import
  traceback.

**`KeyError` for a dataset or pipeline type**

- The class/transform is not registered in the running package, or the config
  uses a name from a different MMDetection generation.
- Start with a built-in type (`CocoDataset`, `VOCDataset`,
  `CityscapesDataset`, `WIDERFaceDataset`, or `CustomDataset`) and only add a
  custom class after its import/registration path is deliberate.

## Optional dependencies

**`albumentations is not installed`**

The `Albu` transform is optional. Remove it for a baseline or install the
source-era optional dependency in the prepared environment. Then verify every
nested transform name, `BboxParams.format`, label field, and mask mapping.
`filter_lost_elements` is handled by the wrapper and should not be assumed to
be a native Albumentations option.

**`imagecorruptions is not installed`**

`Corrupt` cannot run without it. This transform changes pixels only and does
not fix labels. Omit it unless a robustness experiment explicitly requires it.

**`instaboostfast` import failure or missing masks**

`InstaBoost` is not a minimum dependency and expects instance masks. Use a
box-only pipeline without it, or stop and prepare the optional dependency and
mask-compatible dataset separately. Never silently run a mask experiment as
box-only.

## Dataset/config validation

**Manifest validator reports missing images**

- Resolve in this order: `data_root` + relative `img_prefix`, then
  `img_prefix` + record `filename`.
- For VOC, check the split file's IDs against `Annotations/<id>.xml` and
  `JPEGImages/<id>.jpg`. For WIDER, include the XML `folder` in the nested
  image path. For COCO/custom, use the manifest's `file_name`/`filename`.
- Inspect symlink targets with read-only commands. A broken or wrong-split link
  is a path error. Do not create a link from this sub-skill.

**COCO: `KeyError: category_id`, invalid image ID, or empty categories**

Check uniqueness and referential integrity of IDs, category names/order, and
whether the annotation points to the image table rather than a filename. The
reader maps category-table order to labels; model `num_classes` must match the
intended class tuple. Re-run validation with the correct image root.

**COCO: masks fail while boxes work**

A `bbox` alone is not an instance mask. Supply valid polygon/RLE `segmentation`
for each target, keep `with_mask=True`, and collect `gt_masks`. A semantic PNG
map belongs to `seg_prefix`/`with_seg=True`, not to `gt_masks`.

**COCO: annotations are silently absent**

Zero/negative-area boxes, zero-width/height boxes, `ignore`, and `iscrowd`
conditions can remove targets. Training also filters images below the default
minimum dimension and may filter images without ground truth. Compare raw
annotation counts with post-reader counts.

**VOC: `Cannot infer dataset year from img_prefix`**

The legacy class infers the year from a prefix containing `VOC2007` or
`VOC2012`. Use the correct per-year root or a deliberate custom reader; do not
invent a year in the config. Confirm the XML class names are in the fixed VOC
class tuple.

**VOC: XML parse, unknown class, or object shape failure**

Check XML well-formedness, `size/width`, `size/height`, `object/name`,
`difficult`, and all four `bndbox` children. Coordinates are converted from the
XML convention by subtracting one internally. Do not “repair” labels by
clipping them during validation.

**WIDER: images cannot be found although XML exists**

The WIDER reader uses the XML `folder` and image ID to form the filename. Check
that the folder text and image directory agree, that the split list IDs match
XML basenames, and that the selected train/val root is not the dataset parent.
WIDER is a one-class box reader, not an instance-mask reader.

**Custom dataset: `ann`/`bboxes`/`labels` missing**

Inference records may omit `ann`; training records cannot. Ensure boxes are
`N x 4`, labels have length `N`, ignored arrays have matching lengths, and
runtime loading converts JSON lists to the array types expected by transforms.
For custom masks or semantic maps, implement the reader contract explicitly.
Extra JSON keys are not automatically loaded.

## API and CLI misuse

**`FileNotFoundError` after a path looks correct**

Print the effective values, not the source variable names. Relative paths may
have been joined to `data_root` twice, or a filename may already contain an
`images/` prefix. Test the exact resolved annotation and one exact image path.

**Wrong config appears to be used**

`Config.fromfile` executes the selected Python file. In this legacy snapshot,
checked-in examples are flat; there is no evidence for a generic nested
`--cfg-options` command. Use a complete task-owned config, preserve its text,
and do not assume a modern `_base_` merge is available. Runtime flags such as
work directory, resume, validation, GPU count, seed, launcher, output, and
`--eval` do not replace data path edits.

**`Collect` or model forward reports a missing key**

Match the task to the final pipeline:

- detector boxes: collect `img`, `gt_bboxes`, `gt_labels`;
- instance segmentation: also load and collect `gt_masks`;
- inference: inner test transforms generally collect only `img` and metadata.

Check that `DefaultFormatBundle` precedes `Collect` and that every requested
metadata key was added by an earlier transform.

**`LoadAnnotations` fails on a requested field**

`with_bbox`, `with_label`, `with_mask`, and `with_seg` are independent switches.
The dataset's `get_ann_info` must supply the corresponding field. Choose one
semantic: instance masks are per-object; semantic maps are per-pixel.

## Workflow-specific failures

**Training starts but workers repeatedly skip samples**

Crops can return `None` when no ground-truth box remains, and the dataset then
samples another image. Check box scale, crop IoU settings, `min_size`, empty
images, and class labels. Reduce or remove aggressive crops for a diagnostic
run; do not treat a successful process start as a healthy input pipeline.

**Batch collation or shape errors after resize/pad**

Ensure all geometry-bearing fields are registered and transformed together.
Use `Pad(size_divisor=32)` or a deliberate fixed size, not both. Verify channel
order, normalization statistics, and `DefaultFormatBundle`/DataContainer
handling. Large multi-scale settings can exceed memory even with valid data.

**Evaluation uses wrong classes or wrong metric**

COCO evaluation expects COCO-style result/category mapping; VOC evaluation
uses the dataset's class tuple and commonly IoU 0.5. Cityscapes uses its
converted COCO annotation and eight-class mapping. WIDER is face-only. Verify
the evaluation annotation file and dataset config are the same split and class
order used for the checkpoint.

**Distributed or full conversion job fails**

This sub-skill deliberately does not run data downloads, conversion utilities,
distributed launchers, or long training. First pass the safe manifest checks and
a single native sample build. Then hand the conversion/backend job to an
approved workflow with explicit storage, GPU, and recovery controls.

## Minimal triage record

Record:

```text
format / dataset class:
class order and model class count:
split:
effective data_root, ann_file, img_prefix, seg_prefix:
validator command and exit status:
raw images/annotations and post-filter dataset length:
requested target fields and final Collect keys:
installed torch / CUDA / mmcv / optional packages:
first error and exact layer:
conversion or backend work deferred:
```
