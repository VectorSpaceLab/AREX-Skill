---
name: detection
description: "Use for PaddleViT object detection workflows with DETR, Swin, or
  PVTv2: validate COCO data, select configs, build/train/evaluate models, reason
  about transforms, losses, post-processing, and run safe utility smokes.
  Excludes segmentation and generic export; cross-link deployment-and-operations
  for shared runtime concerns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PaddleViT object detection

Use this route for standalone PaddleViT object detection under `object_detection/`:
DETR, Swin, and PVTv2 with COCO boxes. It covers family/config selection,
data preflight, transforms and targets, safe model-contract checks, checkpoint
triage, training/evaluation boundaries, and backend-aware diagnosis. It does
not own semantic segmentation, generic export/inference, quantization, or
weight porting; route those requests to
[deployment-and-operations](../deployment-and-operations/SKILL.md).

The bundled helpers are self-contained and do not import the original source
checkout, download data or weights, or modify a user-owned dataset. A source
checkout is optional and is needed only for a source-model build or native
candidate test. Details that are useful during a focused investigation live in
[model overview](references/model-overview.md),
[data formats](references/data-formats.md),
[workflows](references/workflows.md), and
[troubleshooting](references/troubleshooting.md).

## Route the request

1. Identify the family before changing a config or launching a command:
   - **DETR** for query-based, end-to-end detection with transformer decoder
     queries, Hungarian matching, and direct box post-processing.
   - **Swin** or **PVTv2** for hierarchical backbones feeding FPN, RPN, and
     RoI-style heads with anchors, proposals, and NMS.
2. If the request says only “PaddleViT detection,” ask which family and
   whether the goal is a utility check, source build, evaluation, or training.
   Do not mix family directories in one Python process: common modules such as
   `config`, `coco`, `box_ops`, and `utils` can resolve incorrectly.
3. Keep segmentation separate, even if a request mentions masks or a DETR
   import. For export, predictor, AMP, distributed, or shared runtime issues,
   use [deployment-and-operations](../deployment-and-operations/SKILL.md).

## Preflight before a source run

Validate the **COCO root**, not a split directory. The expected root contains
`annotations/instances_{train,val}2017.json` and the matching
`train2017/` or `val2017/` image directory. Run the read-only helper from the
skill root (replace placeholders with caller-owned values):

```bash
python <skill-root>/scripts/check_coco_layout.py <coco-root> --split val
```

Add `--check-images` to decode referenced images and compare dimensions, or
`--check-api` to parse the annotation through `pycocotools`. Use `--json` for a
machine-readable report and `--demo` for a temporary one-image validator
fixture. A failed check is a stop condition: repair the dataset outside this
skill and rerun; do not download or silently substitute another dataset.

Before importing a source model, run the bounded synthetic contract smoke:

```bash
python <skill-root>/scripts/detection_model_smoke.py --model all --device cpu
```

This checks tiny DETR and four-level anchor-family shapes and finite values. It
is not a source-model build, checkpoint test, COCO test, mAP result, or
benchmark reproduction. Use `--device gpu:0` only when a GPU claim is required
and the backend has already passed its environment probe.

## Select a source root and config

The three projects are standalone. For a source-backed run, enter exactly one
family directory and expose only that directory (and its intended parent) to
imports:

```bash
cd <source-root>/object_detection/DETR   # or Swin or PVTv2
export PYTHONPATH="$PWD:$PWD/..:${PYTHONPATH:-}"
```

Resolve configuration in this order: Python defaults, recursive YAML `BASE`
files, then CLI overrides. Print and inspect the effective config before model
construction. Check backbone output channels against FPN inputs, pyramid
strides and anchor levels, class/category conventions, image divisibility, and
DETR embedding-dimension/head divisibility. Swin/PVTv2 configs preserve the
historical `ROI.NUM_ClASSES` spelling; do not replace it with a guessed key.
The family-specific config and output/target details are in
[model overview](references/model-overview.md) and
[data formats](references/data-formats.md).

## CLI flag contract

The family `main_single_gpu.py` and `main_multi_gpu.py` scripts use these
short, single-dash options:

```text
-cfg PATH             YAML config (BASE files are recursively merged)
-dataset coco         dataset selector
-data_path PATH       COCO root, not train2017/val2017
-batch_size N         per-process/per-GPU batch size
-eval                 evaluation-only mode
-pretrained PREFIX    source appends .pdparams
-resume PREFIX        source expects .pdparams and .pdopt
-last_epoch N         resume epoch metadata
-ngpus N              configured multi-GPU worker count
```

`-cfg=...` and `-cfg ...` are both acceptable. Pass checkpoint **prefixes**
without `.pdparams` when following the source loader. Inspect launcher shell
files rather than executing them blindly: paths, visible devices, output
prefixes, and training duration are caller-owned. A representative command
shape is:

```bash
cd <source-root>/object_detection/DETR
CUDA_VISIBLE_DEVICES=0 python main_single_gpu.py \
  -cfg=./configs/detr_resnet50.yaml -dataset=coco \
  -batch_size=1 -data_path=<coco-root> -eval \
  -pretrained=<checkpoint-prefix>
```

Treat real training/evaluation as expensive and data/checkpoint/GPU dependent;
use the [workflow reference](references/workflows.md) for gated sequencing.

## Family contracts to preserve

- **DETR:** expect logits shaped `[B,Q,C+1]`, normalized center-size boxes
  `[B,Q,4]`, optional auxiliary decoder outputs, and losses including
  classification, L1, and GIoU. Post-processing needs target sizes in
  `[height,width]` order and emits absolute `xyxy` boxes, scores, and labels.
- **Swin/PVTv2:** expect hierarchical features, FPN/RPN/RoI losses during
  training, and post-NMS rows shaped `[label, score, xmin, ymin, xmax, ymax]`
  during evaluation. Their target path uses absolute boxes and contiguous
  classes; the two families share the broad head/neck contract but not every
  backbone channel/config value.
- **All families:** COCO boxes begin as `[x,y,width,height]`; transformations
  must update geometry and area. A valid synthetic training fixture needs at
  least one non-empty target. Preserve original image IDs for COCO results.
  Full transform and output schemas are in the linked references.

## Verification tiers

Choose the cheapest tier that answers the question and record command, device,
Paddle version, config, and result:

1. `check_coco_layout.py` for root layout, JSON arrays, IDs, boxes, files, and
   optional Pillow/COCO-API checks.
2. `detection_model_smoke.py` for standalone tiny shape and finite-value
   contracts; a non-32-divisible size intentionally reports the padding caveat.
3. Native DETR box/transform/model tests when a source checkout and dependencies
   are available. They are evidence candidates, not runtime prerequisites;
   some are skipped or require an untracked fixture.
4. A one-batch source build/forward using one family root and a tiny local
   fixture, only after config/import checks pass.
5. Real COCO evaluation or training only with explicit data, checkpoint, GPU,
   and time approval. Never call a smoke or random-weight forward mAP evidence.

CPU can validate parsing, layout, box utilities, and tiny diagnostics. It does
not establish CUDA, AMP, distributed, or full detector claims. For those
boundaries use [deployment-and-operations](../deployment-and-operations/SKILL.md).

## Stop and recover

- **Missing files/API:** `-data_path` must be the root; verify exact split
  filenames. If `pycocotools` is absent, omit `--check-api` but do not claim
  COCO evaluation is verified.
- **Import/YAML errors:** start a fresh process, isolate one family root,
  resolve `BASE` relative to its YAML, compare keys to that family's config,
  and inspect the final config. Do not mix module paths or claim a build that
  never constructed a model.
- **Shape/checkpoint errors:** verify family, backbone/FPN channels, attention
  divisibility, query/class counts, head spelling, and checkpoint provenance.
  A prefix normally maps to `.pdparams`; resume also needs `.pdopt`. Do not
  reshape incompatible state dictionaries.
- **Bad boxes/empty batches:** inspect crowd flags, category mapping, positive
  area, coordinate format, resize/flip/crop order, and image IDs. Keep one
  valid target in a fixture; an all-empty batch is not a valid smoke.
- **NaN/Inf or no detections:** run CPU geometry checks, verify normalized DETR
  boxes or absolute Swin/PVTv2 boxes, then inspect thresholds, NMS, and loaded
  keys. Random weights cannot support an accuracy claim.
- **CUDA OOM/unavailable:** lower per-GPU batch size or input scale for OOM.
  If CUDA is unavailable, report CPU-only partial evidence; never substitute it
  for a required GPU result. For multi-GPU, check visible devices, `-ngpus`,
  per-process batch semantics, NCCL, and rank gathering before retrying.

See [troubleshooting](references/troubleshooting.md) for expanded recovery
branches. Do not run network, full-native, long-training, or multi-GPU
workflows as part of this route unless explicitly authorized.
