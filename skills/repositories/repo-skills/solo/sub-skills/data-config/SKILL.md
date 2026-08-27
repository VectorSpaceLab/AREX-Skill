---
name: data-config
description: "Prepare, validate, and diagnose legacy SOLO/MMDetection datasets,
  data pipelines, and Python configuration wiring without silently changing
  annotation semantics."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Dataset and configuration operations

Use this sub-skill when a task needs to make SOLO's legacy MMDetection data
loader see the intended images and annotations, or when a config change causes
missing files, empty targets, malformed batches, or evaluation mismatches. It
covers detection and instance-segmentation data wiring; it is not a general
annotation-conversion service.

## Operating contract

Given a dataset root, annotation manifest, dataset type, class list, and the
intended train/validation/test use, produce:

1. a read-only path/schema diagnosis;
2. a config-ready mapping of `data_root`, `ann_file`, `img_prefix`, optional
   `seg_prefix`, and the correct dataset class;
3. a pipeline whose transforms preserve every target field the model consumes;
4. explicit blockers, assumptions, and a small native/runtime check to run
   before expensive training.

Never download data, rewrite annotations, create symlinks, or run a full
conversion as part of validation. From the generated skill root, use the bundled validator for local checks:

```bash
python sub-skills/data-config/scripts/validate_dataset_manifest.py \
  --format coco --ann datasets/example/instances.json --image-root datasets/example/images
```

Use `--format voc`, `--format wider`, or `--format custom` as appropriate; see
[the validator reference](references/data-formats.md#read-only-validator).

## Fast path

1. **Name the contract.** Decide whether the model needs boxes only, instance
   masks, or semantic maps. Record class order, split, image root, annotation
   root, and whether empty images are allowed.
2. **Choose the native reader.** Use `CocoDataset` for COCO JSON and converted
   Cityscapes JSON, `VOCDataset` for VOC XML/split lists,
   `WIDERFaceDataset` for WIDER's VOC-style face XML, or `CustomDataset` only
   for the documented internal list-of-records shape. Do not call a COCO file
   “VOC-compatible” merely because it contains boxes.
3. **Validate before building.** Check JSON/XML structure, IDs, class IDs,
   image dimensions, annotation geometry, and image existence. Broken symlinks
   count as missing paths. The validator is stdlib-only and does not prove that
   the installed native loader, pycocotools, or CUDA operators can run.
4. **Wire paths.** Relative `ann_file`, `img_prefix`, `seg_prefix`, and
   `proposal_file` values are joined to `data_root`; absolute values are not.
   `img_prefix` is then joined to each record's relative `filename`. Keep
   annotation and image roots consistent across every split.
5. **Wire the pipeline.** Training normally loads an image and annotations,
   applies geometry/color transforms, normalizes and pads, formats fields, then
   collects them. Test-time augmentation must end with image tensor conversion
   and collection, not training labels.
6. **Run a tiny native candidate.** Build one dataset/sample or run the
   repository's config parser help in the prepared legacy environment. Defer
   full COCO/Cityscapes conversion and full training until the tiny check is
   clean.

## Dataset-specific decisions

- **COCO:** validate `images`, `annotations`, and `categories`; use
  `segmentation` only when instance masks are required. `bbox` is `[x, y, w, h]`
  and is converted internally to inclusive corner coordinates. `iscrowd` boxes
  are ignored for training targets.
- **Cityscapes:** this release's reader is a COCO subclass with eight classes;
  it expects annotations already converted to COCO JSON and image paths that
  match that JSON. Raw polygon conversion and image flattening are a separate,
  deferred operation.
- **VOC:** split files contain image IDs; XML lives under `Annotations` and
  images under `JPEGImages`. `difficult` objects and configured `min_size`
  objects become ignored. Class names and the inferred year must match.
- **WIDER Face:** the reader expects a split list and VOC-style XML under the
  selected train/val root, with one `face` class. The XML `folder` participates
  in the image filename; check nested image paths rather than assuming a flat
  directory.
- **Custom:** either subclass a known reader with a fixed `CLASSES` tuple or
  provide the internal list of image records. The simple custom contract is
  box detection first; masks or semantic maps require corresponding fields and
  loader logic, not just a new class name.

## Pipeline and config guardrails

- Keep `LoadAnnotations(with_mask=True)` paired with annotations that actually
  carry COCO polygons/RLE or an equivalent custom `masks` field. `with_seg=True`
  instead loads a separate semantic map through `seg_prefix`.
- Geometry transforms must update all registered bbox/mask/seg fields. A crop
  that removes every ground-truth box returns `None`; repeated skips can look
  like a loader hang. `Normalize` belongs after image loading and geometry.
- `Pad(size_divisor=32)` is common for detector backbones. `DefaultFormatBundle`
  and `Collect` define the batch contract; list a mask in `Collect.keys` when
  the model consumes masks.
- The checked-in legacy config corpus is flat and uses `Config.fromfile`; it
  does not provide modern `_base_` or generic `--cfg-options` examples. If a
  local MMDetection/MMCV combination supports inheritance, verify it with that
  parser before using it; otherwise materialize a complete config copy. Do not
  assume a CLI override merged a nested `data.train` field.
- Preset filenames such as `solo_r50_fpn_8gpu_3x.py`,
  `faster_rcnn_r50_fpn_1x_voc0712.py`, `ssd300_wider_face.py`, and
  `faster_rcnn_r50_fpn_1x_cityscapes.py` are illustrative names only. Embed
  the relevant dataset block in the working config and verify its effective
  values rather than asking a future agent to locate a source config.

## Stop conditions and handoff

Stop and report the exact field/path when any of these occurs: an image ID is
unresolved; a category is absent or reordered; a bbox is non-finite, inverted,
or outside the image after the format's coordinate convention; a mask is
requested but unavailable; a split's image and annotation roots are mixed; a
symlink is broken; or an optional transform cannot import. Report whether the
failure is schema, path, config, dependency, or backend-related. Hand off the
validated manifest summary, effective dataset config, pipeline target fields,
validator output, and unresolved conversion boundary.

Read [data-formats.md](references/data-formats.md) for schemas and
[configuration.md](references/configuration.md) for effective config patterns.
For failures, use [troubleshooting.md](references/troubleshooting.md).

## Compatibility and safety note

The source-era installation targets PyTorch 1.1 or newer, CUDA 9 or newer, and
legacy `mmcv==0.2.16`, with pycocotools needed for COCO readers. Optional
Albumentations and imagecorruptions support is not part of the minimum install.
A CPU-only validator proves only local paths and structural checks; it does not
validate custom CUDA kernels or the complete GPU runtime. Keep conversion,
data acquisition, distributed jobs, and source mutation outside this
sub-skill.
