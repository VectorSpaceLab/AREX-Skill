# CLI Reference for `main.py`

## Required flags

- `--cfg FILE`: required YAML config.
- `--data-path PATH`: required for loaders when training/evaluating.

## Mode flags

- No mode flag: train from scratch or from `--pretrained`.
- `--eval`: evaluate and exit after loading `--resume` or `--pretrained` as configured.
- `--throughput`: measure throughput and exit.

## Checkpoint flags

- `--resume`: full checkpoint load for resume/evaluation.
- `--pretrained`: fine-tune load; position-bias and classifier-head handling may be applied.

## Data flags

- `--zip`: use zipped ImageNet loader.
- `--cache-mode no|full|part`: controls zip caching. `part` is common for distributed zipped ImageNet.

## Memory and performance flags

- `--batch-size`: per-GPU batch size.
- `--accumulation-steps`: increase effective batch size without proportional memory growth.
- `--use-checkpoint`: gradient checkpointing, often helpful for larger Swin variants.
- `--disable_amp`: disable PyTorch AMP.
- `--fused_window_process`: only after the optional CUDA extension is built.
- `--fused_layernorm` and `--optim fused_adam|fused_lamb`: require Apex.

## Distributed launcher

Prefer `torchrun` for modern PyTorch. The original scripts also support the older `python -m torch.distributed.launch` style. Under PyTorch 2.x, `LOCAL_RANK` must be set by the launcher before config construction.
