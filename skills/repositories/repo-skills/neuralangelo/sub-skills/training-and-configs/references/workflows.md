# Training workflows

All commands below are intended for a user's Neuralangelo project root. Replace
placeholder paths such as `logs/<group>/<name>` and `projects/neuralangelo/configs/custom/<scene>.yaml`
with project-local paths.

## 1. Minimal preflight before a costly run

```bash
# Summarize inherited YAML and catch strict-override mistakes.
python <skill-dir>/scripts/inspect_config_summary.py \
  --config projects/neuralangelo/configs/custom/<scene>.yaml \
  --project-root . \
  --check-data \
  --override max_iter=2000 \
  --override validation_iter=500 \
  --override checkpoint.save_iter=1000

# Check Python runtime packages without importing Neuralangelo source modules.
python <skill-dir>/scripts/inspect_config_summary.py \
  --config projects/neuralangelo/configs/custom/<scene>.yaml \
  --project-root . \
  --probe-runtime
```

Expected preflight signal:

- Parent chain resolves through `projects/neuralangelo/configs/base.yaml` when a
  DTU, Tanks and Temples, or custom config inherits from it.
- `data.root` points at the prepared dataset directory.
- `data.root/transforms.json` exists and has non-empty `frames` when
  `--check-data` is used.
- If `model.appear_embed.enabled: true`, `data.num_images` is set and matches
  the intended number of training images.
- Runtime probe reports CUDA availability for expensive training and importable
  `torch`, `torchvision`, and `tinycudann`.

If the user only needs COLMAP, video extraction, conversion to `transforms.json`,
or bounding sphere adjustment, stop here and route to `data-preparation`.

## 2. Plan a training command

Use the bundled planner to avoid losing shell quoting or mixing `--resume`,
`--checkpoint`, and config overrides:

```bash
python <skill-dir>/scripts/plan_training_command.py \
  --config projects/neuralangelo/configs/custom/<scene>.yaml \
  --logdir logs/<group>/<name> \
  --gpus 1 \
  --show-pbar \
  --override max_iter=2000 \
  --override validation_iter=500 \
  --override checkpoint.save_iter=1000
```

The planner prints a command like:

```bash
torchrun --nproc_per_node=1 train.py \
  --logdir=logs/<group>/<name> \
  --config=projects/neuralangelo/configs/custom/<scene>.yaml \
  --show_pbar \
  --max_iter=2000 \
  --validation_iter=500 \
  --checkpoint.save_iter=1000
```

For a full single-GPU run that follows the repository's normal launcher style:

```bash
GPUS=1
torchrun --nproc_per_node=${GPUS} train.py \
  --logdir=logs/<group>/<name> \
  --config=projects/neuralangelo/configs/custom/<scene>.yaml \
  --show_pbar
```

For multi-GPU DDP, increase `--nproc_per_node` and ensure the visible CUDA
devices match the count:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 torchrun --nproc_per_node=4 train.py \
  --logdir=logs/<group>/<name> \
  --config=projects/neuralangelo/configs/custom/<scene>.yaml \
  --show_pbar
```

For a true non-DDP single-process launch, pass `--single_gpu`; this is useful
for debugging one visible GPU without initializing distributed training:

```bash
python train.py \
  --single_gpu \
  --logdir=logs/<group>/<name> \
  --config=projects/neuralangelo/configs/custom/<scene>.yaml \
  --show_pbar
```

## 3. Safe smoke run recipe

Before a 500k-iteration run, prove config loading, data loading, model creation,
checkpoint writing, and optional W&B setup with small override values:

```bash
torchrun --nproc_per_node=1 train.py \
  --logdir=logs/smoke/<scene> \
  --config=projects/neuralangelo/configs/custom/<scene>.yaml \
  --show_pbar \
  --max_iter=20 \
  --validation_iter=10 \
  --checkpoint.save_iter=10 \
  --wandb_scalar_iter=10 \
  --wandb_image_iter=10 \
  --data.train.subset=2 \
  --data.val.subset=1
```

Notes:

- `train.py` accepts unknown `--key=value` arguments as config overrides; they
  must match existing inherited keys.
- Keep `data.train.image_size`, `data.val.image_size`, and `model.render.rand_rays`
  realistic enough to expose memory behavior; do not make every smoke run tiny
  if the user is debugging full-resolution OOM.
- `--debug` disables online W&B mode but still exercises most setup code.

## 4. Full training launch

Typical custom scene:

```bash
EXPERIMENT=<scene>
GROUP=<group>
NAME=<run-name>
CONFIG=projects/neuralangelo/configs/custom/${EXPERIMENT}.yaml
GPUS=1

torchrun --nproc_per_node=${GPUS} train.py \
  --logdir=logs/${GROUP}/${NAME} \
  --config=${CONFIG} \
  --show_pbar
```

Useful `train.py` CLI flags:

| Flag | Operational use |
| --- | --- |
| `--config PATH` | Required YAML config. Parents are loaded before overrides. |
| `--logdir DIR` | Output directory for copied final config, checkpoints, W&B files, and traces. |
| `--checkpoint PATH` | Initialize from a checkpoint. With `--resume`, also restore iteration/epoch, optimizer, and scheduler. |
| `--resume` | Resume training state. If no checkpoint is given, the checkpointer tries `latest_checkpoint.txt` in `--logdir`. |
| `--seed INT` | Base seed; training code varies seed by rank. |
| `--local_rank INT` | Normally set by `torchrun` through `LOCAL_RANK`; avoid setting manually unless debugging. |
| `--single_gpu` | Skip distributed initialization. Use with `python train.py` or one visible GPU. |
| `--debug` | Set Imaginaire debug mode and disable online W&B. |
| `--profile` | Enable PyTorch profiler and write a Chrome trace under the logdir. |
| `--show_pbar` | Show tqdm progress bars for train/eval loops. |
| `--wandb` | Enable online W&B logging on the master process. |
| `--wandb_name NAME` | W&B project name passed to `init_wandb`. |

## 5. W&B and logdir behavior

- The final merged config is printed and saved as `logs/<group>/<name>/config.yaml`
  by the master process.
- `--wandb` enables online W&B. Without it, or with `--debug`, W&B mode is
  disabled.
- `--wandb_name` is the W&B project name. With group mode enabled by `train.py`,
  the final two logdir path components become W&B group and run name.
- `wandb_id.txt` is written in the logdir and reused for resume when present.
- Scalars and images are controlled by `wandb_scalar_iter` and
  `wandb_image_iter`; validation is controlled by `validation_iter`.

## 6. Checkpoints, initialization, and resume

Checkpoint files are written into `--logdir`:

- Iteration checkpoints: `epoch_<epoch>_iteration_<iter>_checkpoint.pt`
- Latest pointer: `latest_checkpoint.txt`
- Optional rolling latest model: `latest_checkpoint.pt` when
  `checkpoint.save_latest_iter` is configured.

Initialize weights only:

```bash
torchrun --nproc_per_node=1 train.py \
  --logdir=logs/<group>/<new-name> \
  --config=projects/neuralangelo/configs/custom/<scene>.yaml \
  --checkpoint=logs/<old-group>/<old-name>/<checkpoint>.pt
```

Resume the same run:

```bash
torchrun --nproc_per_node=1 train.py \
  --logdir=logs/<group>/<name> \
  --config=logs/<group>/<name>/config.yaml \
  --resume
```

Resume from an explicit checkpoint:

```bash
torchrun --nproc_per_node=1 train.py \
  --logdir=logs/<group>/<name> \
  --config=logs/<group>/<name>/config.yaml \
  --checkpoint=logs/<group>/<name>/<checkpoint>.pt \
  --resume
```

Use the saved `config.yaml` for exact continuation. Changing model dimensions,
hash-grid dimensions, appearance embeddings, optimizer type, or scheduler shape
can make checkpoint state incompatible.

## 7. Tiny CUDA/runtime checks

These checks do not import Neuralangelo source modules:

```bash
python - <<'PY'
import torch
print('torch', torch.__version__)
print('cuda_available', torch.cuda.is_available())
print('cuda_version', torch.version.cuda)
print('device_count', torch.cuda.device_count())
if torch.cuda.is_available():
    print('device0', torch.cuda.get_device_name(0))
PY

python - <<'PY'
import tinycudann, torchvision
print('tinycudann ok')
print('torchvision', torchvision.__version__)
PY
```

If these fail, fix the training environment before editing configs.
