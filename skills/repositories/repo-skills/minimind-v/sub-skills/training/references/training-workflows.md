# MiniMind-V Training Workflows

## Stage choice

| Stage | Role | Default data | Default base | Freeze | When to choose |
| --- | --- | --- | --- | --- | --- |
| Pretrain | Optional projector alignment | `../dataset/pretrain_i2t.parquet` | `llm` | `freeze_llm=2` | Use when the user wants a separate image-caption warm-up and has Pretrain data. |
| SFT | Main instruction tuning | `../dataset/sft_i2t.parquet` | `pretrain_vlm` by script default | `freeze_llm=1` | Recommended default; can skip Pretrain by using `--from_weight llm`. |

SFT data contains the Pretrain caption subset plus image-instruction and pure-text rows, so Pretrain can be skipped for quick reproduction.

## Single process and DDP

The scripts detect DDP from `RANK` and `LOCAL_RANK`. Under `torchrun`, they initialize NCCL, set `cuda:{LOCAL_RANK}`, use `DistributedSampler`, and wrap with `DistributedDataParallel`.

Example command shapes printed by the bundled builder:

```bash
cd trainer && python train_sft_vlm.py --from_weight llm
cd trainer && torchrun --nproc_per_node 4 train_sft_vlm.py --from_weight llm
```

Use these as user-approved execution commands only after preflight checks and resource approval.

## Freezing strategy

| `freeze_llm` | Effect | Typical use |
| --- | --- | --- |
| `0` | Train all non-vision-encoder parameters | experimental full adaptation; higher memory/risk |
| `1` | Train projector plus first and last LLM layers | SFT default |
| `2` | Train only projector | Pretrain default |

The vision encoder remains frozen and is excluded from saved VLM checkpoint weights.

## Prerequisites

- Tokenizer/model files under `model/`.
- SigLIP2 under `model/siglip2-base-p32-256-ve/`.
- Base LLM weight under `out/llm_768*.pth`.
- SFT/Pretrain parquet files under `dataset/` or custom `--data_path`.
- CUDA-capable torch recommended for real runs.

For lightweight checks, use `build_training_command.py --dry-check-files` and the parquet validator instead of launching training.
