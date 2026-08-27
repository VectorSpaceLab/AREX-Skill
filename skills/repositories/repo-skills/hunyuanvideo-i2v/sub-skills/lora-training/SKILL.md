---
name: "lora-training"
description: "Routes HunyuanVideo-I2V LoRA training tasks, including DeepSpeed
  launcher setup, training hyperparameters, resume/init checkpoints, and the
  dataset expectations that come from the latent-extraction workflow."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# LoRA Training

Use this sub-skill when the user wants to train, resume, or debug a LoRA effect model for HunyuanVideo-I2V.

## What Belongs Here

- Running or adapting the DeepSpeed LoRA launcher.
- Choosing training hyperparameters and memory-saving flags.
- Resuming from an experiment directory or checkpoint.
- Checking whether the processed latent dataset is in the right layout.
- Understanding where the final `pytorch_lora_kohaya_weights.safetensors` file appears.

## What Does Not Belong Here

- Building the latent dataset from raw videos. Use [`../data-preparation/SKILL.md`](../data-preparation/SKILL.md).
- Single-image inference or xDiT generation. Use [`../inference/SKILL.md`](../inference/SKILL.md).

## Read First

- [`references/workflows.md`](references/workflows.md) for the canonical train/resume flow.
- [`references/cli-reference.md`](references/cli-reference.md) for the verified training flags.
- [`references/api-reference.md`](references/api-reference.md) for the data loader and helper functions that govern the training schema.
- [`references/troubleshooting.md`](references/troubleshooting.md) for DeepSpeed, checkpoint, and dataset issues.
- [`../../references/checkpoints.md`](../../references/checkpoints.md) because training loads the same checkpoints as inference.

## Bundled Script

- [`scripts/run_lora_training.py`](scripts/run_lora_training.py) — build or execute the canonical DeepSpeed command safely. It lives under `$SKILL_ROOT`; invoke it from `$CHECKOUT_ROOT` with `--repo-root "$CHECKOUT_ROOT"`. Use `--dry-run` first. Install `requirements-optional.txt` only when this GPU workflow is actually selected.

## Typical Workflow

Commands run from the real checkout root; `$SKILL_ROOT` is not the checkout:

1. Confirm the checkpoint tree with `$SKILL_ROOT/scripts/check_checkpoint_layout.py --ckpts-root "$CHECKOUT_ROOT/ckpts" --mode train`.
2. Confirm the processed latent dataset layout with `$SKILL_ROOT/sub-skills/data-preparation/scripts/check_dataset_layout.py`.
3. Print the canonical DeepSpeed command with `$SKILL_ROOT/sub-skills/lora-training/scripts/run_lora_training.py --repo-root "$CHECKOUT_ROOT"`.
4. Add `--execute` only when the GPU memory and dataset paths are ready.
5. Inspect the run directory for `args.json`, logs, and the LoRA checkpoint.
## Constraints to Remember

- The README documents 79GB for 360p LoRA training.
- `task-flag` and `output-dir` are required by the training script.
- The launcher expects the processed latent dataset, not raw videos.
- The base model, VAE, and text encoders are loaded before the first training step.
