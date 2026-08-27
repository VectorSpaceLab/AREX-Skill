# Distributed Training Commands

`timm` distributed CLI usage is a thin wrapper around PyTorch DDP. The repository shell helper is equivalent to `torchrun --nproc_per_node=N train.py ...`.

## Shell Helper Equivalence

The helper accepts the process count as its first argument, shifts it away, and forwards every remaining argument to `train.py`:

```bash
./distributed_train.sh 4 --data-dir /data/imagenet --model resnet50 --batch-size 128 --amp
```

Equivalent explicit command:

```bash
torchrun --nproc_per_node=4 train.py --data-dir /data/imagenet --model resnet50 --batch-size 128 --amp
```

Use the explicit `torchrun` form when the helper file is missing, when adapting commands outside a checkout, or when adding multi-node rendezvous options.

## Single-Node DDP Pattern

```bash
torchrun --nproc_per_node=NUM_GPUS train.py \
  --data-dir DATA_ROOT \
  --model MODEL \
  --batch-size PER_PROCESS_BATCH \
  --workers WORKERS_PER_PROCESS \
  --amp
```

Important details:

- `--batch-size` is per process/GPU, not total global batch.
- Effective global batch size is `batch_size * world_size * grad_accum_steps`; training uses this for automatic learning-rate scaling when `--lr` is omitted.
- The training script initializes distributed state from the launcher environment and accepts `--local_rank` for compatibility, but modern `torchrun` primarily supplies environment variables.
- Use one process per GPU for normal DDP. Avoid combining DDP with `--num-gpu`; `--num-gpu` belongs to validation/inference DataParallel style commands, not standard training DDP.

## Multi-Node Pattern

Use PyTorch rendezvous arguments before `train.py`:

```bash
torchrun \
  --nnodes=2 \
  --nproc_per_node=8 \
  --rdzv_backend=c10d \
  --rdzv_endpoint=HOST0:29500 \
  train.py \
  --data-dir /data/imagenet \
  --model resnet50 \
  --batch-size 128 \
  --workers 8 \
  --amp
```

All nodes need compatible code, package versions, dataset visibility, and network access to the rendezvous endpoint. Make output paths shared or rank-safe according to the execution environment.

## Distributed BatchNorm and Augmentation Flags

| Concern | Flags | Guidance |
| --- | --- | --- |
| Distributed BN stats | `--dist-bn reduce|broadcast|""` | Default is `reduce`; use empty string to disable post-epoch BN stat distribution. |
| SyncBatchNorm | `--sync-bn` | Converts BN layers for synchronized training; do not combine with split BN or torchscript. |
| Split BN | `--split-bn`, `--aug-splits`, `--resplit` | Use for AugMix/JSD-style recipes; requires valid split setup. |
| Augmentation repeats | `--aug-repeats` | Distributed-training-only repetition control. |
| Gradient accumulation | `--grad-accum-steps` | Increases effective batch without increasing per-process memory. |

## CPU and Debug Caveats

`torchrun` can launch CPU processes, but most practical timm DDP examples assume CUDA. For command debugging, prefer a single-process CPU command first:

```bash
python train.py --data-dir tiny-imagenet-layout --model resnet18 --batch-size 2 --device cpu --workers 0 --epochs 1 --no-aug
```

Then switch to DDP once the dataset, model, and output paths are correct.

## Common Failure Modes

- Missing `distributed_train.sh`: use `torchrun --nproc_per_node=N train.py ...` directly.
- Hangs at startup: verify `NUM_GPUS`, rendezvous host/port, firewall, matching environment variables, and one process per visible GPU.
- Wrong learning rate after scaling GPUs: explicitly set `--lr`, or recalculate expected effective batch and `--lr-base*` values.
- CUDA rank/device mismatch: ensure `CUDA_VISIBLE_DEVICES` exposes exactly the intended devices and that launcher process count matches them.
- BatchNorm mismatch: disable `--sync-bn` or `--split-bn` combinations that violate script assertions.
- OOM on DDP: reduce per-process `--batch-size`, use `--grad-accum-steps`, consider `--amp`, reduce image size, or disable memory-heavy augmentation/model options.
