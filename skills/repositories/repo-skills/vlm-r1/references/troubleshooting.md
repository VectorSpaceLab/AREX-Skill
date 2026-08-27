# Cross-cutting troubleshooting

Use this page before drilling into a sub-skill-specific troubleshooting reference.

## Install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No module named open_r1` | The nested `open-r1` distribution is not installed in the active Python environment. | Install the VLM-R1 multimodal package in the environment the user will use, then run `python -c "import open_r1"`. |
| `No module named utils` when importing or running `open_r1.grpo_jsonl` as a module | `grpo_jsonl.py` uses the source-layout import `from utils.math import compute_score`. | Run from a source layout that places `open_r1/utils` on `PYTHONPATH`, or patch the import to `from open_r1.utils.math import compute_score` before relying on package-module execution. |
| `ImportError: Glm4vForConditionalGeneration` | GLM module requires a Transformers class missing from the pinned `transformers==4.49.0` stack. | Do not use GLM for Qwen/InternVL tasks. If GLM is required, install a compatible Transformers/model stack and smoke-test `glm_module.py` before training. |
| `deepspeed` import complains about missing `CUDA_HOME` or `nvcc` | GPUs are visible but the environment lacks compiler/toolkit discovery needed by DeepSpeed op checks. | Point `CUDA_HOME` to a compatible toolkit with `bin/nvcc`, install an environment-local nvcc package, or choose a DeepSpeed/torch path that does not need JIT-compiling those ops. |
| `flash_attn` build/import failure | Python/torch/CUDA ABI mismatch or missing compiler/build deps. | Install a wheel matching the exact torch/CUDA/Python stack, or switch `--attn_implementation` away from `flash_attention_2` when supported. |

## Data and path failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Number of data files must match number of image folders` | `--data_file_paths` and `--image_folders` colon-separated lists have different lengths. | Use the data validator and training launcher dry-run to check counts before running `torchrun`. |
| `Image paths do not exist` | JSONL `image` values are relative to each paired image folder, not to the command's current directory. | Validate a small sample with `data-and-rewards/scripts/validate_jsonl_dataset.py --image-folders ...`. |
| Reward stays zero for bbox tasks | Answer is missing `<answer>` tags, malformed JSON/fenced JSON, wrong bbox coordinate frame, or wrong `reward_method`. | Use the data/reward reference and offline bbox scorers to check exact answer format and IoU behavior. |
| GUI multi-image task sees only one image | JSONL row uses a string instead of list, or prompt placeholders do not match image count. | Use list-valued `image` for multi-image rows and validate with the data sub-skill. |

## Backend/runtime failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| CUDA out of memory | Batch size, num generations, max completion length, model size, FlashAttention, or reference model memory exceeds GPU VRAM. | Reduce `--per_device_train_batch_size`, `--num_generations`, or `--max_completion_length`; use ZeRO-3/offload or LoRA/freeze vision; consider smaller models or more GPUs. |
| Training resumes unexpectedly or refuses to start fresh | `--resume_from_checkpoint True` and `output_dir` already contains `checkpoint-*`. | Decide whether to resume or start with a clean output directory; inspect rendered command before execution. |
| W&B prompts or logging failures | `--report_to wandb` is active but account/API setup is missing. | Use `--no-wandb`/`--report_to none` for local dry-runs, or configure W&B explicitly. |
| Multi-node hang | Wrong `MASTER_ADDR`, port blocked, rank/node count mismatch, NCCL networking issue. | Render per-node commands with `render_multinode_torchrun.py`, verify ranks and rendezvous address, then check cluster networking/NCCL. |
| Ascend service cannot start | Missing NPU device nodes, driver/CANN mismatch, Docker bind mounts absent, or XLLM build incomplete. | Use the Ascend sub-skill troubleshooting page; do not treat CUDA checks as Ascend readiness. |

## Safe escalation pattern

1. Run the smallest bundled checker for the task: environment probe, JSONL validator, command renderer, model-module static checker, offline bbox scorer, or Ascend template renderer.
2. Fix validation failures before launching expensive jobs.
3. Confirm required model, data, hardware, credentials, output directories, and runtime budget.
4. Only then execute full training/evaluation/server commands.
