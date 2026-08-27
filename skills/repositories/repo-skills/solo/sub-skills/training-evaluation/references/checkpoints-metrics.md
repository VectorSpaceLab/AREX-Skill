# Checkpoints, model selection, and metrics

## Select a config/checkpoint pair

The SOLO README identifies the implementation as based on MMDetection v1.0.0
and lists SOLO, Decoupled SOLO, and SOLOv2 families. The `configs/solo/`
files encode the family in `model.type`/head type and commonly use 8-GPU
names, for example `solo_r50_fpn_8gpu_1x.py`, `solo_r50_fpn_8gpu_3x.py`,
`solo_r101_fpn_8gpu_3x.py`, and decoupled variants. Treat the filename as a
hint, not proof of compatibility.

Choose in this order:

1. Match the task: SOLO instance masks require a mask-capable config and
   `segm`; a box detector does not become an instance segmenter by changing the
   metric.
2. Match the family/head, backbone, input pipeline, class count, and training
   schedule to the checkpoint metadata and intended comparison.
3. Match the data protocol: model-zoo references are COCO 2017 train/val (with
   some README results described as minival) and use fixed normalization and
   resize conventions. A custom dataset needs its own baseline.
4. Check hardware and latency constraints. The README reports model-zoo time
   and AP values for specific GPU/input protocols; they are not portable
   guarantees.

The model-zoo README table includes, among other entries, SOLO R50 1x/3x,
SOLO R101 3x, Decoupled SOLO R50/R101, and lightweight variants. It reports AP
and testing time but does not make those values acceptance thresholds. Network
URLs are evidence of published artifacts only; do not download them without
explicit user approval.

## `load_from` versus `resume_from`

- **Resume**: `tools/train.py --resume_from <path>` assigns the checkpoint to
  `cfg.resume_from`. The training runner restores model parameters, optimizer
  state, and epoch. Use after interruption when the original experiment should
  continue.
- **Load**: config `load_from` supplies model weights while the new run starts
  from epoch 0. Use for finetuning or transfer, after verifying architecture,
  class head, and preprocessing compatibility.
- **Checkpoint metadata**: `tools/train.py` records MMDetection version,
  config text, and dataset class names when checkpoint metadata is enabled.
  Evaluation falls back to `dataset.CLASSES` for old checkpoints without
  `CLASSES`; that fallback can hide a class-order mismatch, so check it
  explicitly.

Keep `latest`/epoch checkpoints and logs together, but never infer that
`latest.pth` is the best metric checkpoint. Select a checkpoint using an
explicit validation metric and epoch policy, and record that policy. Recovery
from a failed or resumed run begins by separating the log/checkpoint lineage;
do not overwrite the only copy or continue after a class, optimizer, or epoch
mismatch has been observed.

## COCO-style metrics

The legacy evaluator accepts:

- `bbox`: box detection AP/AR.
- `segm`: instance-mask AP/AR, the primary metric for SOLO mask quality.
- `proposal` and `proposal_fast`: proposal recall metrics, not class-aware
  detection AP.
- `keypoints`: only for a compatible keypoint dataset/model.

COCO summary values commonly include AP (IoU 0.50:0.95), AP50, AP75, APs,
APm, APl, AR1, AR10, AR100, ARs, ARm, and ARl. Report the exact split, metric,
class set, max detections, and whether evaluation used a clean or corrupted
pipeline. A higher AP on a different split or a changed class mapping is not a
valid regression claim.

For VOC-like datasets, robustness code supports bbox evaluation at a supplied
IoU threshold; it does not imply that VOC and COCO AP are interchangeable.
Class-wise analysis requires a compatible annotation/result utility and is
reference-only when those tools require extra data or output conversions.

## Logs and training signals

The legacy text logger writes JSON-lines records with fields such as `epoch`,
`iter`, `mode`, `time`, losses, memory, and evaluation metrics. Inspect:

- loss terms: monotonic trend is not required, but persistent NaN/Inf or
  exploding values is a stop condition;
- `time`: separate first-iteration loader/warmup effects from steady-state
  throughput;
- `memory`: compare peak values with available GPU memory, not just process
  RSS;
- validation AP: align metric names and epoch boundaries with the schedule;
- missing/duplicated epochs: often indicate truncated logs, multiple jobs
  writing one file, or a resumed run that was not separated.

The repository's `tools/analyze_logs.py` excludes the first time value of each
epoch by default for average iteration time and can plot scalar loss values or
mAP-like epoch values. The bundled helper is safer for automation because it
has no plotting dependency and emits bounded CSV/summary output.

## Reproducibility record

For each comparison retain:

```text
config path and effective overrides
checkpoint path, hash, and metadata
train/eval dataset split and annotation version
metric names and evaluator options
GPU count, device ids, batch/workers, and FP16 setting
seed/determinism flags and exact command
log/output paths and stop reason
```

Do not report model-zoo AP, FPS, or memory as reproduced unless the local
protocol matches the source protocol closely enough to justify the claim.
