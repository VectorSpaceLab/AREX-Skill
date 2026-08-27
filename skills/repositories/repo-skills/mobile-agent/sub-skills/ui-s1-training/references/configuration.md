# UI-S1 Runtime Configuration

## Required live training prerequisites

- CUDA-capable GPUs sized for the chosen model and batch/rollout settings.
- Compatible PyTorch, Transformers, flash-attn, Ray, vLLM or SGLang, and UI-S1/verl installation.
- Qwen/Qwen2.5-VL model checkpoint available locally or through an approved download/cache.
- Train/val JSONL files validated with this sub-skill.
- Free ports for Ray head/worker processes.
- Logging backend (`console`, `swanlab`, or private alternative) configured without leaking tokens.

## Environment variables from example scripts

- `NCCL_DEBUG=INFO`
- `TORCH_NCCL_ASYNC_ERROR_HANDLING=1`
- `PYTHONFAULTHANDLER=1`
- `HYDRA_FULL_ERROR=1`
- `VLLM_USE_V1=1`
- `MASTER_ADDR`, `MASTER_PORT`, `WORLD_SIZE`, `RANK` for distributed runs.

## Laptop/CPU-only warning

A command built for UI-S1 does not mean it is safe to run on a laptop. Public examples often assume 8 GPUs. If `--gpus-per-node` is lowered, also revisit rollout count, batch sizes, sequence lengths, tensor parallel size, and memory utilization. CPU-only hosts can validate JSONL and command strings only.
