# Training And Evaluation Workflows

This reference turns the documented MapTR launch contracts into a guarded
procedure. Commands are templates: replace `PROJECT_ROOT`, `CONFIG`,
`CHECKPOINT`, `N`, and `RUN_ID` only after the preflight gates pass. Do not
paste a template into a scheduler until its paths, process count, and backend
are proven.

## Evidence And Compatibility Gate

The repository's training guide gives these canonical distributed forms:

```bash
./tools/dist_train.sh ./projects/configs/maptr/maptr_tiny_r50_24e.py 8
./tools/dist_test_map.sh ./projects/configs/maptr/maptr_tiny_r50_24e.py ./path/to/ckpts.pth 8
```

The wrappers set `PYTHONPATH` to the project root, invoke
`python3 -m torch.distributed.launch`, use `--launcher pytorch`, and accept
extra arguments after the GPU count. Training defaults to port `28509` and
appends `--deterministic`; MapTR test defaults to port `29503` and appends
`--eval chamfer`. `PORT` in the shell environment overrides those defaults.
The bundled `scripts/launch_distributed.py` prints an equivalent argv without
shell interpolation and uses dry-run as its default.

Before any expensive command, confirm all of the following:

- The exact config exists and its base files can be resolved.
- Its `data_root`, train/val/test annotation files, map annotation file, camera
  assets, and any pretrained backbone path exist. Conversion belongs to the
  data-preparation skill; do not regenerate it here.
- For `plugin=True`, the project plugin is importable. Configs use
  `projects/mmdet3d_plugin`; MapTR also depends on legacy mmdetection3d,
  mmcv-full custom ops, and GeometryKernelAttention. A visible CUDA device is
  not evidence that these versions or extensions work.
- The checkpoint is readable and corresponds to the same model topology,
  dataset class mapping, point sampling, and relevant config. For evaluation,
  a trained MapTR checkpoint is required; for a new training run, the config's
  backbone initialization must be available if it is not intentionally
  disabled.
- `N` does not exceed the number of GPUs assigned and visible to the process.
  Check the scheduler allocation and `CUDA_VISIBLE_DEVICES`, not just host
  hardware. On one visible GPU, use `N=1`.
- Disk space is sufficient for one merged config, timestamped logs, periodic
  checkpoints, temporary distributed result collection, and formatted JSON.
- The intended output directory is unique or an explicit resume/update is
  approved.

If any gate is unknown, stop with a preflight report. Do not use a failed
training attempt as a dependency probe.

## Zero-Cost Parser And Config Checks

From the project root, first run:

```bash
python tools/train.py --help
python tools/test.py --help
python tools/misc/print_config.py projects/configs/maptr/maptr_tiny_r50_24e.py
python scripts/launch_distributed.py --help
python scripts/launch_distributed.py train --help
python scripts/launch_distributed.py test --help
```

Expected observations:

- the train parser lists `--work-dir`, `--resume-from`, `--no-validate`,
  `--gpus`/`--gpu-ids`, `--seed`, `--deterministic`, `--launcher`,
  `--autoscale-lr`, and `--cfg-options`;
- the test parser lists a positional config/checkpoint, `--eval`,
  `--eval-options`, `--out`, `--format-only`, `--show`, `--show-dir`,
  distributed collection options, seed/deterministic, and `--cfg-options`;
- the printed tiny config includes plugin loading, three map classes
  (`divider`, `ped_crossing`, `boundary`), 20 fixed points, 900 queries, 50
  vectors, BEV dimensions 200x100, `queue_length=1`, `evaluation.metric` set
  to `chamfer`, FP16 loss scale 512, and the expected data paths;
- the bundled validator describes dry-run and `--execute` behavior.

`print_config.py` only loads/merges the config and prints it. It is not a
proof of data availability, Python package compatibility, custom-op loading,
checkpoint compatibility, or GPU memory capacity.

## Single-Process Training

Use this only when the legacy stack and model path are already proven for a
single GPU. It is a training command, not a cheap smoke test:

```bash
python tools/train.py \
  projects/configs/maptr/maptr_tiny_r50_24e.py \
  --work-dir work_dirs/RUN_ID \
  --gpus 1 \
  --seed 42 \
  --deterministic \
  --launcher none
```

`--work-dir` wins over a config `work_dir`; otherwise the script uses
`./work_dirs/<config-basename>`. With `--launcher none`, the script is
non-distributed and sets `cfg.gpu_ids` from `--gpus` or `--gpu-ids`. Avoid
claiming that `--gpus 2` is distributed: it is still the non-distributed path.
Prefer one process/GPU unless the implementation and memory plan explicitly
support otherwise.

Useful safe overrides (quote values containing brackets, commas, or spaces):

```bash
python tools/train.py CONFIG.py \
  --work-dir work_dirs/RUN_ID \
  --gpus 1 --seed 42 --deterministic \
  --cfg-options data.workers_per_gpu=1
```

The old `--options key=value` spelling is accepted but deprecated. Do not pass
both `--options` and `--cfg-options`. `--cfg-options` is merged into the
loaded config before plugin import and model/data construction, so validate
that a changed key is intentional and syntactically accepted by mmcv.

`--autoscale-lr` scales the configured optimizer learning rate by
`len(cfg.gpu_ids)/8` before distributed initialization. Treat this as a
scientific change, record it, and do not combine it casually with a manually
changed learning rate.

## Distributed Training

The source launcher contract is:

```bash
PORT=28509 \
PYTHONPATH="PROJECT_ROOT:$PYTHONPATH" \
python3 -m torch.distributed.launch \
  --nproc_per_node=N --master_port=PORT \
  PROJECT_ROOT/tools/train.py CONFIG.py \
  --launcher pytorch EXTRA_ARGS --deterministic
```

Use the safe bundled validator to construct this form:

```bash
python scripts/launch_distributed.py train \
  --project-root PROJECT_ROOT \
  --config projects/configs/maptr/maptr_tiny_r50_24e.py \
  --gpus 1 --port 28509 \
  -- --work-dir work_dirs/RUN_ID --seed 42
```

Its default output is a shell-escaped, informational command. Inspect it and
then rerun with `--execute` only after an explicit human decision to allocate
GPU resources. The wrapper's deterministic flag is forced to match the source
launcher; do not treat a duplicated user flag as a second reproducibility
mode.

Distributed training calls `init_dist('pytorch', **cfg.dist_params)`, where
MapTR defaults to NCCL. The process count must match an allocated, visible GPU
set. A scheduler may expose a non-contiguous device list; use the scheduler's
assigned visibility and do not invent device ids in this skill.

## Distributed Chamfer Evaluation

The checked-in `tools/test.py` builds the test dataset, wraps the model in a
multi-GPU distributed wrapper, loads the checkpoint on CPU first, and then
runs the custom multi-GPU test path. Its non-distributed branch currently
asserts false, so use the distributed launcher even when `N=1`:

```bash
python scripts/launch_distributed.py test \
  --project-root PROJECT_ROOT \
  --config projects/configs/maptr/maptr_tiny_r50_24e.py \
  --checkpoint work_dirs/RUN_ID/epoch_24.pth \
  --gpus 1 --port 29503 \
  -- --seed 42 --deterministic
```

This produces the equivalent of:

```bash
PYTHONPATH="PROJECT_ROOT:$PYTHONPATH" \
python3 -m torch.distributed.launch \
  --nproc_per_node=N --master_port=29503 \
  PROJECT_ROOT/tools/test.py CONFIG.py CHECKPOINT \
  --launcher pytorch EXTRA_ARGS --eval chamfer
```

The MapTR dataset evaluator accepts `chamfer` and `iou`. For `chamfer`, it
computes AP at thresholds `0.5`, `1.0`, and `1.5`, averages per class, and
reports `NuscMap_chamfer/mAP` plus per-class detail keys. The default project
configuration and `dist_test_map.sh` select `chamfer`. `bbox` is not a
supported metric in these map dataset evaluators; a request for it must be
repaired before launch (see [troubleshooting.md](troubleshooting.md)).

The test script sets `jsonfile_prefix` below a timestamped
`test/<config-name>/` path when rank zero evaluates. The dataset formatter
creates `nuscmap_results.json` and may create/update the configured map ground
truth annotation file if it is absent. Ensure the output parent is writable
and keep the resulting JSON with the exact config/checkpoint record.

## Training State, Loading, And Resume

MapTR's default runtime config starts with `load_from=None` and
`resume_from=None`; the training script overwrites `cfg.resume_from` only when
`--resume-from` names an existing regular file. The custom training helper
then gives `resume_from` priority over `load_from`:

- `--resume-from CHECKPOINT` restores runner state, including epoch/optimizer
  state when present. Validate the file before launch; a missing path is not a
  safe way to request a resume because the entry point simply does not set it.
- `load_from` loads model weights without the promise of full optimizer/runner
  continuity. A config `pretrained` field is generally backbone initialization
  for a new model, not a resume operation.
- Keep the config aligned with the checkpoint's model type, number/order of map
  classes, fixed point count, BEV geometry, plugin variant, and dataset
  pipeline. The dumped config beside a completed run is the strongest local
  provenance record.

For a resume command:

```bash
python scripts/launch_distributed.py train \
  --project-root PROJECT_ROOT \
  --config projects/configs/maptr/maptr_tiny_r50_24e.py \
  --checkpoint work_dirs/RUN_ID/epoch_12.pth \
  --gpus 1 \
  -- --work-dir work_dirs/RUN_ID --resume-from work_dirs/RUN_ID/epoch_12.pth
```

The validator treats `--checkpoint` as the required checkpoint input for
`test`; for `train`, it is an optional preflight file and does not add a
resume flag by itself. Pass the training entry point's `--resume-from`
explicitly after `--` so the intended state transition is visible.

If the checkpoint was produced with another process count, loader, optimizer,
FP16 setting, or config, do not assume exact continuation. Reconcile the
recorded merged config first; if it cannot be reconciled, start a new run in a
new work directory and label it as such.

## Validation During Training And FP16

The 24-epoch MapTR configs use a workflow of training and an evaluation config
with interval 2 and metric `chamfer`. Training's `--no-validate` disables
checkpoint evaluation during training. It does not disable checkpoint writes
or make the model/data/backend cheaper to initialize.

Most MapTR configs set:

```python
fp16 = dict(loss_scale=512.)
optimizer_config = dict(grad_clip=dict(max_norm=35, norm_type=2))
checkpoint_config = dict(interval=1)
```

Values vary by config; inspect the merged printout. The training helper wraps
the optimizer with `Fp16OptimizerHook` when `fp16` is present. Do not claim
that disabling FP16 is a harmless memory switch: it changes numerical
behavior and may interact with the legacy attention code. If FP16 overflows,
produces NaNs, or fails in a custom op, stop, preserve the log/config, and
only test a separately documented config change after deciding how that affects
comparability.

## Expected Outputs And Stop Rules

At startup, expect environment information, distributed status, the merged
config, seed/deterministic status, and model text in the log. During training,
logger output follows `log_config.interval` (normally 50 iterations), and
checkpoints follow `checkpoint_config.interval`. These are expected observations
rather than a successful-result claim.

Stop without retrying when:

- a required asset, annotation, map file, checkpoint, custom op, or package
  version is missing;
- the requested process count exceeds visible/allocated GPUs;
- a resume config changes model/data semantics or the checkpoint cannot be
  identified;
- an OOM persists after one conservative reduction of workers or batch size
  and no approved resource plan exists;
- the command would overwrite an unrelated work directory or result;
- a launch error indicates incompatible legacy binaries rather than a missing
  user argument.

Preserve logs and partial checkpoints on interruption. Do not call an
interrupted run complete; inspect the last checkpoint and resume only after
reconciling its config and state.
