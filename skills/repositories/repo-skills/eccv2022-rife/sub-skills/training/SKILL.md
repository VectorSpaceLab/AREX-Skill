---
name: training
description: "Operate ECCV2022-RIFE training preflight, Vimeo triplet data
  layout, distributed CUDA/NCCL launch, TensorBoard logs, checkpoints, and
  resource planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ECCV2022-RIFE training sub-skill

Use this sub-skill when the user asks how to train or reproduce ECCV2022-RIFE, prepare the Vimeo90K triplet layout, plan a distributed CUDA launch, interpret `world_size` and batch size, locate training checkpoints/logs, or diagnose TensorBoard, NCCL, CUDA, and OOM failures.

Route away from this sub-skill when the user asks for image/video interpolation CLI usage, official benchmark interpretation, or model-architecture changes beyond the public `Model.update` training contract.

## Safety boundary

Full training is long-running, mutates the checkout, requires a Vimeo triplet dataset, and uses CUDA/NCCL. Do not start training automatically during routine assistance. Safe default actions are:

1. Validate the dataset layout with [`scripts/check_vimeo_triplet_layout.py`](scripts/check_vimeo_triplet_layout.py).
2. Confirm CUDA-enabled PyTorch, TensorBoard, available GPUs, and the intended process count.
3. Build or review the launch command without executing it.
4. Ensure output directories and checkpoint-overwrite expectations are explicit.

Run the actual distributed command only after the user confirms data availability, GPU allocation, wall-time budget, and that writing `train_log/flownet.pkl`, `train/`, and `validate/` is acceptable.

## Primary references

- [`references/training.md`](references/training.md) — data layout, launch commands, arguments, checkpoint/log outputs, evaluation loop, and resource planning.
- [`references/troubleshooting.md`](references/troubleshooting.md) — missing data, TensorBoard, CUDA/NCCL, rank/world-size, OOM, checkpoint overwrite, and long-run safety issues.
- [`scripts/check_vimeo_triplet_layout.py`](scripts/check_vimeo_triplet_layout.py) — safe no-training validator for `vimeo_triplet` list files and sampled `im1.png`/`im2.png`/`im3.png` sequence files.

## Operating checklist

When handling a training request:

1. **Clarify intent**: preflight only, single-GPU smoke planning, full reproduction, resumed/continued experiment, or post-training benchmark use.
2. **Check data**: require `vimeo_triplet/tri_trainlist.txt`, `vimeo_triplet/tri_testlist.txt`, and `vimeo_triplet/sequences/<clip>/im1.png`, `im2.png`, `im3.png` for listed clips. The loader uses the first 95% of `tri_trainlist.txt` for training and the remaining 5% for validation.
3. **Check runtime**: training is CUDA-only in this checkout (`torch.device("cuda")`, NCCL process group, DDP when `local_rank != -1`). TensorBoard is required by `train.py` but is not listed in the base requirements file.
4. **Plan launch**: keep `--world_size` equal to the launcher process count. The README pattern is `python3 -m torch.distributed.launch --nproc_per_node=4 train.py --world_size=4`.
5. **Plan resources**: default `--epoch 300`, per-process `--batch_size 16`, and data-loader workers can make a run expensive. The README reports 16 CPUs, 4 GPUs, and about 20G memory for training.
6. **Confirm side effects**: checkpoints save to `train_log/flownet.pkl` after every epoch, overwriting the same filename; TensorBoard event files go to `train/` and `validate/`.
7. **Post-training routing**: for metrics, use the evaluation sub-skill; for applying a produced checkpoint to images or videos, use the interpolation sub-skill.
