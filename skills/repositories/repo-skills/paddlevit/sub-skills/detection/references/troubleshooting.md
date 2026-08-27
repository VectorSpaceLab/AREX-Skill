# Detection troubleshooting

## Dependency and import failures

- **`No module named pycocotools`**: install `pycocotools` in the active
  environment, then run `python -c "from pycocotools.coco import COCO; print('ok')"`.
  The layout checker can still validate JSON/files without `--check-api`, but
  dataset construction and COCO mAP cannot be called verified.
- **`No module named config/coco/box_ops`**: use one standalone family source
  root as the current directory and `PYTHONPATH`; repeated module names make a
  mixed `PYTHONPATH` unsafe.
- **main module creates output or logs during import**: expected from the
  source's top-level argument/config setup. Invoke the script, or inspect
  configs/source files rather than importing the main module in a probe.
- **Paddle version/API error**: record Python/Paddle versions and reduce to a
  tiny CPU operation or the bundled standalone smoke. The source targets
  Paddle 2.1-era APIs; Paddle 2.6.2 is installed evidence, not proof that all
  old code paths are compatible.

## COCO and target failures

- **FileNotFoundError**: `-data_path` must be the root containing
  `annotations/`, `train2017/`, and `val2017/`. Check the exact source-resolved
  filename `instances_{split}2017.json`.
- **JSON/API load error**: validate top-level arrays, unique image/category
  IDs, annotation references, bbox numeric values, and optional `segmentation`
  encoding. Run `check_coco_layout.py --check-api` before invoking a model.
- **No samples / empty batch**: the source removes images without bbox
  annotations and excludes crowd/invalid boxes. Inspect `iscrowd`, positive
  width/height, image references, and category references. Include one valid
  target in every synthetic training fixture.
- **Wrong boxes after resize/flip/crop**: remember input COCO boxes are
  `[x,y,w,h]`, source preparation changes them to corners, DETR normalization
  changes them to center-size, while Swin/PVTv2 retain absolute corners.
  Check coordinate order and `[height,width]` versus `[width,height]` metadata.

## Config and shape failures

- **YACS unknown key or missing `DATA_PATH`**: compare the family config's
  exact field names. DETR declares `DATA.DATA_PATH`; Swin/PVTv2 historically
  declare `VAL_DATA_PATH` but CLI update writes `DATA_PATH` after defrosting.
  Confirm this behavior in the installed YACS version and inspect the final
  config. Prefer a YAML override/local compatibility fix over silently
  changing a model module.
- **FPN channel mismatch**: feature stage channels must match `FPN.IN_CHANNELS`.
  Swin and PVTv2 YAMLs are not interchangeable. Verify `OUT_CHANNELS` and
  strides too.
- **Attention reshape error**: DETR embedding dimension must divide evenly by
  `NUM_HEADS`; do not use a checkpoint/config pair from another model.
- **RoI class/shape error**: Swin/PVTv2 heads use the historical key
  `ROI.NUM_ClASSES` and expect contiguous class IDs. `MODEL.NUM_CLASSES` is not
  necessarily the head class count.
- **Checkpoint mismatch**: source checkpoint arguments are prefixes. For
  `-pretrained=/x/model`, the code expects `/x/model.pdparams`; resume expects
  both `.pdparams` and `.pdopt`. Verify key names and architecture before
  loading; never reshape incompatible tensors to force a load.

## Loss and post-processing failures

- **NaN/Inf losses**: check non-empty boxes, normalized DETR values in
  `[0,1]`, positive areas, finite images, and valid GIoU inputs. Reduce batch
  size or disable one augmentation only as a diagnostic.
- **No predictions**: inspect score threshold, NMS threshold/top-k, checkpoint
  loading, and class mapping. Random-weight output is not a meaningful
  detection result.
- **COCO evaluator rejects predictions**: use original image IDs; provide
  absolute `xyxy` boxes, scores, and contiguous/local labels as expected by the
  family's adapter; ensure `pycocotools` loaded the same annotation file.
- **mAP changes between single/multi GPU**: verify per-GPU batch size,
  distributed sampler tail handling, all-rank gather, and that each image ID is
  evaluated once.

## Hardware and operations

- **CUDA unavailable**: use CPU for JSON, parser, box, and tiny model smoke
  only. Mark GPU-dependent training/evaluation as blocked or unverified.
- **CUDA OOM**: lower per-process batch size and image scale first; then review
  workers/accumulation. Multi-GPU multiplies process count but does not make a
  single process's activation footprint smaller.
- **NCCL/distributed launch failure**: verify visible device count, `-ngpus`,
  one-node process setup, and the selected `main_multi_gpu.py`; do not switch
  to CPU and label it a multi-GPU pass.
- **Export/inference request**: route to
  `../deployment-and-operations/SKILL.md`; this sub-skill intentionally
  excludes generic export.
