---
name: "training"
description: "Launch, resume, and troubleshoot OpenFlamingo training runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# training

Use this sub-skill for OpenFlamingo training and fine-tuning tasks: configuring model and data flags, generating launch commands, selecting DDP or FSDP, resuming checkpoints, and diagnosing runtime failures.

## Read first

- [CLI reference](references/cli-reference.md)
- [Data formats](references/data-formats.md)
- [Training workflows](references/training-workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Safe command builder](scripts/build_train_command.py)

## What this sub-skill covers

- Vision encoder, language model, tokenizer, and cross-attention setup.
- LAION and MMC4 WebDataset inputs.
- DDP, Slurm-style launches, Horovod, and FSDP caveats.
- Precision, gradient checkpointing, loss weighting, and checkpointing.
- W&B logging, offline mode, and restart behavior.

## Typical flow

1. Confirm the LAION and MMC4 shard layouts and sample counts.
2. Pick DDP or FSDP and decide whether to use `--dataset_resampled`.
3. Generate a launch command with `scripts/build_train_command.py`.
4. Run the printed command from the repository root or another shell environment that can resolve the training entrypoint path.
5. Monitor `run_name/checkpoint_<epoch>.pt` and resume with `--resume_from_checkpoint` when needed.

## Guardrails

- Do not launch full training from this skill without explicit user intent and the required data and model weights.
- If the language model uses tied input/output embeddings, prefer DDP or freeze LM embeddings when using FSDP.
- Keep LAION and MMC4 batch counts aligned; the training loop asserts equal batches per epoch.
- If the shard metadata is missing, supply explicit sample counts for both datasets.
