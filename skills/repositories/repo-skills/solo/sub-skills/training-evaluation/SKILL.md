---
name: training-evaluation
description: "Plan and safely run SOLO/MMDetection-era training, checkpoint
  evaluation, log analysis, robustness benchmarking, and experimental FLOPs
  measurements, with explicit CUDA, data, distributed, and legacy dependency
  caveats."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Training and evaluation

Use this skill when the researcher needs to train a SOLO detector, evaluate a
local checkpoint, compare model-zoo baselines, inspect JSON training logs,
measure robustness to image corruptions, or estimate model complexity. This is
an operational guide for the PyTorch/MMDetection v1-era implementation, not a
claim that a modern MMDetection release is API-compatible.

## Route the request

Choose one path before running an expensive command:

- **Train**: a config, writable work directory, compatible dataset, and CUDA
  GPUs are required. Start with a bounded smoke or a resumed run; do not start
  a 1x/3x schedule merely to test installation.
- **Evaluate**: a matching config, local checkpoint, and test dataset are
  required. Use the repository's legacy instance-segmentation evaluator for
  SOLO masks and its generic detector evaluator for bbox/mask tasks. Save a
  `.pkl` or COCO JSON output.
- **Analyze logs**: use the bundled `scripts/analyze_log.py` for a safe local
  JSON-lines summary or bounded CSV export. It does not import MMDetection or
  access a checkout.
- **Robustness**: use the repository's legacy corruption-evaluation entry point
  only after clean evaluation works and `imagecorruptions` plus the corruption
  benchmark data/pipeline are available. It is single-GPU in the documented
  workflow and is expensive.
- **FLOPs/parameters**: use the repository's legacy FLOPs entry point only for
  a CUDA-capable, locally importable config. Treat the result as experimental,
  shape-dependent, and incomplete for unsupported/custom operators.

Read [references/commands-and-checklists.md](references/commands-and-checklists.md)
for generic path-safe templates and preflight checks. Read
[references/checkpoints-metrics.md](references/checkpoints-metrics.md) for
checkpoint semantics and metric interpretation. Read
[references/robustness-and-flops.md](references/robustness-and-flops.md) for
benchmarking limits. Read
[references/troubleshooting.md](references/troubleshooting.md) when anything
fails.

## Hard prerequisites and boundaries

- This repository targets **PyTorch 1.1 or higher**, with the documented
  legacy stack centered on **CUDA 9.x+ and MMCV 0.2.16 (`mmcv==0.2.16`)**. The
  installation docs say PyTorch >=1.5 was not tested; newer stacks may need
  adaptation.
- Full training and dataset evaluation normally need CUDA, compiled/custom
  operators, local annotations/images, and substantial time/storage. A CPU
  import or config parse does **not** validate custom CUDA kernels, distributed
  behavior, or end-to-end metrics.
- Never download weights or datasets implicitly. Require user-supplied local
  paths and verify them before launching work. Keep outputs outside source
  files; use a dedicated work directory.
- Do not use publishing, upgrade, conversion, Slurm, or distributed shell
  helpers as if they were harmless diagnostics. Their side effects and
  environment assumptions are documented only as boundaries here.

## Config and dataset preflight

Before train or test, inspect the selected config and its effective values:

1. Confirm the model family/head, `data_root`, train/val/test annotation files,
   image prefixes, class count, test pipeline, batch size, workers, `work_dir`,
   `total_epochs`, `lr_config`, `workflow`, `checkpoint_config`, and
   `dist_params.backend`.
2. This checkout's configs are mostly self-contained Python configs rather than
   modern `_base_` inheritance graphs. If a user config uses inheritance,
   resolve every parent in the same environment and record the effective merged
   values; do not assume a current MMDetection config loader understands it.
3. For COCO-style data, expect `annotations/instances_*.json` alongside the
   corresponding image directories under the configured root. SOLO training
   collects `img`, `gt_bboxes`, `gt_labels`, and `gt_masks`; a test pipeline
   collects only image inputs. Check that annotation class ids and configured
   classes agree.
4. Check that a checkpoint belongs to the same model/head and preprocessing
   contract. A readable `.pth` is not necessarily compatible.

## Run only after preflight

Single-GPU command shape (substitute the selected checkout's legacy entry-point
command; the generated skill does not depend on that checkout being present):

```bash
<TRAIN_ENTRY_POINT> <CONFIG.py> --work_dir <WORK_DIR> --gpus 1
<INSTANCE_EVAL_ENTRY_POINT> <CONFIG.py> <CHECKPOINT.pth> --out <RESULTS.pkl> --eval segm
<DETECTOR_EVAL_ENTRY_POINT> <CONFIG.py> <CHECKPOINT.pth> --out <RESULTS.pkl> --eval bbox segm
```

For a visual test, add `--show` only when a display is available; headless
sessions should save artifacts instead. In this legacy interface, an
instance-evaluation `--json_out` value is a filename prefix rather than a
normal `.json` output path; prefer `--out` and `--eval` for the simplest
reproducible result artifact.

For distributed execution, use the environment's supported launcher or a
reviewed equivalent rather than copying a cluster command blindly. The
following is conceptual argument shape, not a command to paste without a
reviewed entry point:

```text
<DISTRIBUTED_LAUNCHER> <TRAIN_ENTRY_POINT> <CONFIG.py> --launcher pytorch --work_dir <WORK_DIR>
<DISTRIBUTED_LAUNCHER> <DETECTOR_EVAL_ENTRY_POINT> <CONFIG.py> <CHECKPOINT.pth> --launcher pytorch --out <RESULTS.pkl> --eval bbox segm --tmpdir <TEMP_DIR>
```

Use one process per GPU, an NCCL-compatible CUDA setup, a unique rendezvous
port per concurrent job, and a shared/readable output location. Confirm rank-0
is the only process writing final aggregate outputs. Multi-GPU evaluation may
use CPU temporary collection or GPU collection; both need communication and
sufficient temporary space.

## Training decisions and stop conditions

- The published baseline learning rate assumes 8 GPUs × 2 images/GPU
  (effective batch size 16). If the effective batch changes, use the documented
  linear scaling rule only as an explicit experiment; `--autoscale-lr` scales
  against 8 GPUs for the non-distributed training path.
- `resume_from` restores model weights, optimizer state, and epoch for an
  interrupted run. `load_from` restores weights only and starts training from
  epoch 0, which is the finetuning behavior. Do not substitute one for the
  other.
- Stop before full training when data paths, class mapping, config construction,
  checkpoint compatibility, CUDA/custom-op import, or the first bounded loss
  step is unresolved. Stop an active run on persistent NaN/Inf loss, corrupted
  checkpoints, data leakage or annotation mismatch, rank desynchronization,
  repeated OOM after reducing the planned batch, or a metric that cannot be
  compared under the same dataset/config/checkpoint protocol.
- Preserve the config text, exact command, environment versions, seed,
  checkpoint filename, log JSON, and evaluation output with each result.

## Metrics and interpretation

Use `bbox` for box AP/AR, `segm` for instance-mask AP/AR, `keypoints` only for a
compatible task, and proposal metrics only when proposals are the intended
output. COCO reports AP, AP50, AP75, APs, APm, APl and AR variants; compare the
same metric, split, class set, max detections, preprocessing, and checkpoint.
SOLO model-zoo numbers are COCO/minival-era reference points, not acceptance
thresholds for a new dataset. Report clean performance before corrupted-data
performance, and do not compare throughput or FLOPs across different input
shapes, hardware, operator coverage, or post-processing conventions.

## Verification boundary

Safe candidates are parser-help for the selected legacy training/evaluation
entry point and a tiny local JSON log run through
`scripts/analyze_log.py`. Do not claim that these checks validate training,
COCO metrics, distributed synchronization, FP16 stability, or custom CUDA
kernels. Full training, COCO/VOC evaluation, robustness sweeps, model-zoo
weight downloads, and FLOPs runs remain user-approved, data/backend-dependent
experiments.
