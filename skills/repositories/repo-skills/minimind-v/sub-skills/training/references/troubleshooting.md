# Training Troubleshooting

## Missing parquet or weights

Use `build_training_command.py --dry-check-files` and `validate_vlm_parquet.py`. For SFT without Pretrain, set `--from_weight llm` so the script looks for base LLM weights rather than `pretrain_vlm`.

## Missing SigLIP2/tokenizer

Training initialization needs tokenizer files and the frozen SigLIP2 directory. Route acquisition to `data-and-resources`; do not start downloads by default.

## CUDA unavailable or OOM

Training is GPU-oriented. Confirm torch backend, reduce batch size, use gradient accumulation, avoid `torch.compile` until the baseline works, and ask before launching or relaunching costly runs.

## DDP/rank problems

Use `torchrun --nproc_per_node N` so `RANK` and `LOCAL_RANK` are set. NCCL requires CUDA; if CPU-only, do not use DDP. Ensure every rank sees the same data and resource paths.

## Checkpoint mismatch

Missing/unexpected keys often mean wrong `hidden_size`, `num_hidden_layers`, `use_moe`, or checkpoint prefix. MoE weights require `_moe` suffix and `--use_moe 1`.

## Logging issues

`--use_wandb` imports SwanLab as a W&B-compatible logger. If login/network/service access is unavailable, disable logging or configure credentials explicitly.
