# Training workflows

## A. No-side-effect parser and contract checks

Run these first from the repository root and from the active environment:

```bash
python skills/disco/diffusion-planner/sub-skills/model-training/scripts/check_training_contract.py --help
python skills/disco/diffusion-planner/sub-skills/model-training/scripts/check_training_contract.py \
  --check-normalization normalization.json \
  --predicted-neighbor-num 10
```

The bundled checker is stdlib/numpy-only and does not train, download, import
the model, or mutate checkpoints. The long-running trainer is intentionally
not bundled: it writes checkpoints/logs and depends on a generated corpus and
an application-specific execution context. Apply these checks before a
separately managed entrypoint that accepts the documented flags.

## B. Validate a model-ready handoff

A valid handoff has a data directory and a JSON list. Every list value is a
filename relative to the data directory:

```text
/data/dp/train/
  map_token_0001.npz
  map_token_0002.npz
/data/dp/train.json       # ["map_token_0001.npz", "map_token_0002.npz"]
```

Check a few records before workers are launched:

```bash
python skills/disco/diffusion-planner/sub-skills/model-training/scripts/check_training_contract.py \
  --check-manifest /data/dp/train \
  --data-list /data/dp/train.json \
  --future-len 80 --time-len 21 \
  --agent-num 32 --predicted-neighbor-num 10 \
  --static-objects-num 5 --lane-num 70 --lane-len 20 \
  --route-num 25 --route-len 20 --limit 8
```

The checker reports all checked files, shape/key errors, and non-finite values.
It does not require nuPlan or rewrite files. If the original data producer has
more neighbor rows, that is acceptable: the dataset slices past/future
neighbors for the configured limits. Feature dimensions and temporal/map axes
must still match the model contract.

## C. One-GPU API/data smoke

Use a tiny fixture and explicit CPU or one GPU only to check parser/data/model
wiring. This is not a training benchmark. For a training entrypoint smoke, use
`--ddp false`, `--num_workers 0`, `--use_data_augment false`, a tiny manifest,
and a temporary save directory; stop if the command proceeds into an epoch
unless the user explicitly approved a CUDA smoke. Full training is CUDA/NCCL
oriented.

A safe model-config check should use the same architecture values as the
checkpoint's `args.json`; do not shrink only some token dimensions while
reusing a full checkpoint. A useful assertion set for a synthetic forward is:

```text
input batch B=2
encoder context token count = agent_num + static_objects_num + lane_num
sampled trajectories = (B, 1 + predicted_neighbor_num, 1 + future_len, 4)
diffusion time = (B,)
training score output = (B, 1 + predicted_neighbor_num, 1 + future_len, 4)
```

If a CPU model smoke triggers a missing nuPlan vehicle-parameter import through
augmentation, disable augmentation and route the result as an API limitation,
not as proof that the full training environment is healthy.

## D. Single-node eight-GPU DDP

Use the active environment's interpreter, never the checked-in shell's
`sudo`/placeholder path:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
python -m torch.distributed.run \
  --standalone --nnodes 1 --nproc-per-node 8 \
  <training-entrypoint> \
  --train_set /data/dp/train \
  --train_set_list /data/dp/train.json \
  --normalization_file_path /data/dp/normalization.json \
  --save_dir /runs/dp --name dp-baseline \
  --batch_size 2048 --port 22323
```

The documented implementation splits the global batch as `2048 // 8 = 256`
per rank. Before invoking the separately managed entrypoint:

- ensure `batch_size % 8 == 0`;
- ensure exactly eight visible devices for `--nproc-per-node 8`;
- use a free port and do not leave an older torchrun job exporting rank
  variables in the same shell;
- make the data, normalization file, and save directory visible/writable to
  every rank;
- keep all model shape flags identical across ranks.

The source launcher evidence exports eight GPUs and invokes
`torch.distributed.run`, but it contains placeholders and `sudo`; copy only
its high-level launch semantics into the separately managed entrypoint.

## E. Resume a run

A normal run looks like:

```text
/runs/dp/training_log/dp-baseline/2025-.../
  args.json
  latest.pth
  model_epoch_20_trainloss_....pth
  tb/
```

Resume by passing the directory containing `latest.pth`:

```bash
python -m torch.distributed.run --standalone --nnodes 1 --nproc-per-node 8 \
  <training-entrypoint> \
  --train_set /data/dp/train --train_set_list /data/dp/train.json \
  --normalization_file_path /data/dp/normalization.json \
  --resume_model_path /runs/dp/training_log/dp-baseline/2025-... \
  --save_dir /runs/dp --name dp-baseline-resume --port 22324
```

Resolve `<training-entrypoint>` to the separately managed trainer for the
current application environment; this skill does not direct a future agent to
open or execute a source-checkout script. The implementation's
`resume_model` appends `latest.pth`, restores model and any available
optimizer/schedule/epoch/W&B/EMA keys, and starts at the saved epoch. If the
argument is a `.pth` file, the resulting `...pth/latest.pth` lookup fails.
If the checkpoint has only a bare model state dict, model loading can succeed
but optimizer/scheduler/EMA/epoch state will be absent; record that limitation.

## F. Controlled training adaptations

Prefer changing one contract at a time:

- **smaller experiment**: reduce `batch_size`, `train_epochs`, and data list;
  keep all feature axes and the checkpoint architecture consistent;
- **no augmentation**: `--use_data_augment false`;
- **EMA adaptation**: do not merely pass `--use_ema false`; the current
  entrypoint leaves `model_ema` undefined and `train_epoch` calls
  `ema.update(model)` unconditionally. Initialize/guard EMA in a reviewed code
  patch, then verify the save path and checkpoint keys;
- **offline logging**: leave `--use_wandb false` or set the W&B mode through
  the environment only after confirming the logger's writable path;
- **loader diagnosis**: `--num_workers 0 --no-pin-mem`;
- **single process**: `--ddp false`, one visible GPU, and a batch size that is
  already the desired local batch (there is no world-size division in the
  fallback path).

The scheduler factory named `CosineAnnealingWarmUpRestarts` provides linear
warmup then a fixed multiplicative phase in this checkout; do not infer cosine
decay from its name. The optimizer is AdamW and gradients are clipped to norm
5 before `optimizer.step()`.
