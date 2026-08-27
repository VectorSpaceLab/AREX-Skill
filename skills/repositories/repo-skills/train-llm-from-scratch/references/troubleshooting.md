# Cross-Cutting Troubleshooting

Use this root reference for install/import/backend/checkpoint triage. Then route
to the nearest sub-skill for workflow-specific recovery.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError` for `src`, `config`, `data_loader`, or `ui` | Package is not installed in the active environment, or the command is not run from a compatible checkout. | Install with `pip install -e .` in the selected environment. For UI imports, add `.[ui]`; for dataset downloads and W&B, add `.[train]`. |
| `ModuleNotFoundError` for `tiktoken`, `h5py`, `datasets`, `streamlit`, `altair`, or `wandb` | Missing base dependency or optional extra. | Install the narrow extra that owns the missing surface: base/core for tokenizer/HDF5, `[train]` for datasets/W&B, `[ui]` for Streamlit charts. |
| `torch.cuda.is_available()` is false even on a GPU host | CPU-only torch build, driver/container passthrough problem, or unsupported wheel. | Verify `python -c 'import torch; print(torch.__version__, torch.version.cuda)'`; install a torch CUDA build matching the host; rerun `scripts/check_environment.py --backend cuda`. |
| CPU smoke passes but full training fails on CUDA | CPU smoke validates math/imports only; full runs need CUDA memory, bf16/DDP, and correct data paths. | Run a tiny CUDA model smoke, then route memory/DDP issues to `sub-skills/model-pretraining/` or `sub-skills/post-training-rlhf/`. |
| CUDA out of memory during pretraining or RLHF | Model/context/batch too large; attention materializes large `(B, heads, T, T)` tensors; another job uses the GPU. | Lower per-GPU batch, use grad accumulation, reduce context for smoke, free other jobs, or use the UI GPU-busy guard. See workflow troubleshooting in sub-skills. |
| `torchrun` hangs or logs only one rank | DDP launch/environment issue, rank not reaching cleanup, or mixed single/multi-process assumptions. | Reproduce with one process first. Use `torchrun --standalone --nproc_per_node=N` only for stages designed for DDP. Check rank-0 logs and route to the owning training sub-skill. |
| Checkpoint shape mismatch | Checkpoint `cfg` architecture differs from requested model dimensions, or legacy checkpoint lacks modern `cfg`. | Inspect with `scripts/inspect_checkpoint.py`; do not guess model size for production evaluation/training. |
| Reward/value checkpoint has extra keys | Reward/PPO wrappers add heads or prefixes. | Generation/evaluation loaders may filter to backbone keys. Strict training resumes still need the correct wrapper type; route to post-training or evaluation sub-skill. |
| Data file exists but training loss is nonsensical | Wrong schema, all-zero/all-one SFT mask, invalid preference pairs, wrong RL gold, or context truncation. | Stop training and validate with `sub-skills/data-preparation/scripts/*`. Regenerate or clean data before continuing. |
| GSM8K evaluation cannot load data | `datasets` extra missing, cache unavailable, or network denied. | Install `[train]` and confirm data/cache policy. If network is not allowed, only build dry-run commands and skip real GSM8K. |
| W&B failure stops logging concern | W&B is optional and logger falls back to JSONL on import/init errors. | Keep `use_wandb=false` unless credentials/network are configured. Use JSONL metrics as the durable record. |
| Streamlit launch fails | Missing `[ui]` extra, wrong environment, or port/session issue. | Install `.[ui]`, run `streamlit run ui/app.py`, and use the configuration/UI sub-skill for job registry/logs. |

## Route by root cause

- Data schema, masks, token IDs, preference rows, RL prompts:
  [`sub-skills/data-preparation/SKILL.md`](../sub-skills/data-preparation/SKILL.md)
- Base architecture, pretraining, checkpoints, memory, DDP:
  [`sub-skills/model-pretraining/SKILL.md`](../sub-skills/model-pretraining/SKILL.md)
- SFT/RM/DPO/PPO/GRPO losses, rewards, KL, rollout, metrics:
  [`sub-skills/post-training-rlhf/SKILL.md`](../sub-skills/post-training-rlhf/SKILL.md)
- GSM8K eval, answer parsing, chat/raw generation:
  [`sub-skills/evaluation-chat/SKILL.md`](../sub-skills/evaluation-chat/SKILL.md)
- JSON configs, smoke configs, Streamlit UI, metrics JSONL and job registry:
  [`sub-skills/configuration-ui/SKILL.md`](../sub-skills/configuration-ui/SKILL.md)

## Safe escalation order

1. Reproduce with `--print-config`, `--help`, or a dry-run bundled command
   builder.
2. Validate data and inspect checkpoints before loading large models.
3. Run root `scripts/check_environment.py` and the relevant sub-skill smoke
   helper.
4. Only then launch long data downloads, training, multi-GPU jobs, or real GSM8K
   evaluation.
