# Cross-Cutting Troubleshooting

## Install or Import Fails

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: swift` | `ms-swift` is not installed in the active Python | Install with `pip install ms-swift -U` or install the local source checkout with `pip install -e .`. |
| `swift` command not found | Console scripts are not on `PATH` or package install did not complete | Run `python -m pip show ms-swift`, use the same environment's `python -m pip install -U ms-swift`, then reopen/refresh the shell. |
| `swift eval` fails importing EvalScope | Evaluation extra is missing | Install evaluation support before using `swift eval`; route details to `export-evaluation`. |
| `megatron ...` fails importing Megatron packages | Megatron optional stack is missing | Install the Megatron extra or documented Megatron dependencies only for Megatron workflows; route details to `advanced-rl-distributed`. |
| vLLM/SGLang/LMDeploy import error | Accelerated serving backend not installed or incompatible | Choose `--infer_backend transformers` for broad compatibility or install the selected backend with matching CUDA/Python support. |

## Model and Dataset Downloads

- ms-swift defaults to ModelScope for model and dataset access; use `--use_hf true` when HuggingFace should be the source.
- For international ModelScope access, configure the documented ModelScope domain environment variable when needed.
- For offline work, use local model and dataset paths. If the local model would otherwise be checked against a hub, set the documented model-check flag to avoid network validation.
- If a model loader needs a helper Git repository, download that dependency separately and pass the documented local-repository path argument.
- Never paste hub tokens into shared commands or scripts; use environment variables or a private shell session.

## CLI and Config Problems

- YAML/JSON configs are expanded into command-line arguments. If an `ENV` key conflicts with an existing environment variable, the existing environment wins.
- Use JSON strings for dict-like CLI values and repeated values for lists.
- If a command behaves like training but should be plain pretraining, check whether `swift pt` or `--use_chat_template false --loss_scale all` is intended.
- If a route unexpectedly starts distributed execution, check `NPROC_PER_NODE`, `NNODES`, `MASTER_PORT`, `NODE_RANK`, and `MASTER_ADDR` in the environment.

## Hardware and Backend Issues

- CUDA OOM during training: reduce `--max_length`, batch size, generated tokens, image/video pixel caps, or enable memory-saving training features such as gradient checkpointing, packing, padding-free, DeepSpeed, or FSDP where appropriate.
- Multimodal OOM: set `MAX_PIXELS`, `VIDEO_MAX_PIXELS`, and `FPS_MAX_FRAMES`; for vLLM also tune model length, number of sequences, GPU memory utilization, and multimodal prompt limits.
- Accelerated inference backend rejects a model: verify backend model support separately from ms-swift model support; fall back to `transformers` when uncertain.
- NPU or vendor accelerators: use the vendor-specific visibility variable and package stack; do not assume CUDA wheels apply.
- Flash-attention, DeepSpeed, vLLM, LMDeploy, SGLang, and quantization packages can be sensitive to Python, CUDA, torch, and GPU architecture.

## Workflow Selection Errors

- Dataset row errors belong in `data-model-customization` before tuning hyperparameters.
- Adapter/full checkpoint confusion belongs in `training` for checkpoint semantics and `inference-deployment` for runtime loading.
- Merge/quantization decisions belong in `export-evaluation`, especially when a serving backend is the goal.
- GRPO reward or rollout placement issues belong in `advanced-rl-distributed`, not ordinary inference/deployment.
- EvalScope failures belong in `export-evaluation`, even when evaluation is triggered during training.
