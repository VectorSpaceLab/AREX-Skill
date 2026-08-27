# Training and evaluation commands

These are generic templates. Replace every angle-bracket value with a local,
user-approved path or entry point. They do not assume a source checkout path,
network access, scheduler, or private environment. The source evidence uses
legacy training/evaluation entry points; the generated skill does not bundle
those long-running, checkout-specific programs. Keep their flags aligned with
the selected installation's parser and run `--help` before a real job.

## Preflight

```bash
python - <<'PY'
from pathlib import Path
config = Path('<CONFIG.py>')
checkpoint = Path('<CHECKPOINT.pth>')
for label, path in [('config', config), ('checkpoint', checkpoint)]:
    print('{}: {} exists={}'.format(label, path, path.exists()))
if checkpoint.exists():
    print('checkpoint_bytes:', checkpoint.stat().st_size)
PY

# Replace each placeholder with the reviewed entry point in your checkout.
<TRAIN_ENTRY_POINT> --help
<DETECTOR_EVAL_ENTRY_POINT> --help
<INSTANCE_EVAL_ENTRY_POINT> --help
<ROBUSTNESS_ENTRY_POINT> --help
<FLOPS_ENTRY_POINT> --help
```

The help checks still import the legacy dependencies; if import fails, diagnose
the environment before interpreting the result. Some old programs may fail
after parsing help because dependencies are imported at module load time. Do
not turn a help failure into a full run.

For config review, inspect the file as Python/MMCV configuration in the target
environment and record the effective values. At minimum verify:

| Area | Required observation |
|---|---|
| Model | detector type, backbone/head, `num_classes`, custom/DCN/ROI operators |
| Data | `dataset_type`, annotation paths, image prefixes, train/val/test split, test mode |
| Pipeline | train mask/bbox annotations, normalization, resize/padding, test transforms |
| Runtime | `work_dir`, `total_epochs`, `workflow`, checkpoint interval, logging interval |
| Optimizer | optimizer type/LR, warmup and step schedule, gradient clipping |
| Devices | `imgs_per_gpu`, workers, `device_ids`, `dist_params.backend`, FP16 block |

For an inheritance-based user config, resolve parent files and overrides first.
The v1-era configs represented by this skill are commonly standalone Python
files; do not invent a `_base_` chain where none exists.

## Single-GPU training

```bash
<TRAIN_ENTRY_POINT> <CONFIG.py> \
  --work_dir <WORK_DIR> \
  --gpus 1 \
  --seed <INTEGER> \
  --deterministic
```

Omit seed flags when reproducing the published stochastic setup exactly.
`--gpus` applies to non-distributed training in the legacy parser; it is not a
replacement for a distributed launcher. Add `--validate` only after the
validation dataset and evaluator are known to work.

For an interrupted run:

```bash
<TRAIN_ENTRY_POINT> <CONFIG.py> \
  --work_dir <WORK_DIR> \
  --resume_from <CHECKPOINT.pth>
```

Use `--resume_from` for continuation. To finetune from weights without the old
optimizer/epoch state, set the config's `load_from` (or create a reviewed local
override) rather than treating resume as finetuning.

## Multi-GPU training and evaluation

A launcher must start one process per GPU and provide a working process group.
Use the local installation's reviewed distributed entry point; this conceptual
shape is not a command to paste without a reviewed launcher:

```text
<DISTRIBUTED_LAUNCHER> <TRAIN_ENTRY_POINT> <CONFIG.py> --launcher pytorch --work_dir <WORK_DIR>
<DISTRIBUTED_LAUNCHER> <DETECTOR_EVAL_ENTRY_POINT> <CONFIG.py> <CHECKPOINT.pth> --launcher pytorch --out <RESULTS.pkl> --eval bbox segm --tmpdir <TEMP_DIR>
```

Distributed shell/Slurm wrappers are intentionally not bundled: they have
process, port, scheduler, and external-state assumptions. Set a distinct
`PORT` for concurrent jobs, ensure every rank can read the config/checkpoint/
data and write temporary results, and make rank 0 the only writer of final
aggregate outputs.

## Detector and SOLO evaluation

Generic detector evaluation:

```bash
<DETECTOR_EVAL_ENTRY_POINT> <CONFIG.py> <CHECKPOINT.pth> \
  --out <RESULTS.pkl> \
  --eval bbox segm
```

SOLO instance-segmentation evaluation:

```bash
<INSTANCE_EVAL_ENTRY_POINT> <SOLO_CONFIG.py> <CHECKPOINT.pth> \
  --out <RESULTS.pkl> \
  --eval segm
```

The legacy parser exposes `proposal`, `proposal_fast`, `bbox`, `segm`, and
`keypoints`, but a model/dataset may not support every choice. `--out` must end
in `.pkl` or `.pickle`. `--show` is display-oriented and may fail on headless
hosts; prefer saved results for reproducible evaluation.

The evaluator builds the test dataset, disables pretraining during model
construction, optionally wraps an FP16 model, and loads the checkpoint before
running on the selected device. A failure can therefore arise during
config/data construction, checkpoint loading, or iteration/custom operators.

## Log analysis

For the bundled checkout-independent helper, run from the generated skill root
or adjust the path to the installed skill directory:

```bash
python sub-skills/training-evaluation/scripts/analyze_log.py <LOG.json> --summary
python sub-skills/training-evaluation/scripts/analyze_log.py <LOG.json> --metric loss_cls --out <CURVE.csv>
python sub-skills/training-evaluation/scripts/analyze_log.py <LOG.json> --metric bbox_mAP --out <CURVE.csv>
python sub-skills/training-evaluation/scripts/analyze_log.py <LOG.json> --time --include-outliers
```

The helper accepts JSON Lines records with at least `epoch`; values may be
scalars or lists. It writes CSV rather than opening a GUI and bounds file size,
line count, and record count. The original source-era log tool groups records
by epoch, treats mAP-like metrics as epoch curves, and otherwise plots
iteration values; use it only when its optional plotting semantics are
explicitly required.

## Robustness and FLOPs templates

```bash
<ROBUSTNESS_ENTRY_POINT> <CONFIG.py> <CHECKPOINT.pth> \
  --out <ROBUST_RESULTS.pkl> --eval bbox segm \
  --corruptions noise --severities 0 1 2

<FLOPS_ENTRY_POINT> <CONFIG.py> --shape <HEIGHT> <WIDTH>
```

Start robustness with one corruption/severity after clean evaluation. The
robustness output is a pickle plus an aggregate sidecar. FLOPs constructs a
model and dummy forward on CUDA in the source workflow; it is not a CPU-only
parser.

## Stop and capture

At every stop, save the command, exit status, config/checkpoint hashes if
available, package versions, GPU count, dataset split, output paths, and the
first actionable traceback. Stop instead of retrying when the same failure
shows a bad path, incompatible classes, missing required backend, invalid
metric, corrupted checkpoint, or a non-finite training signal.
