---
name: training
description: "Choose and launch StyleTTS2 first-stage training, second-stage
  training, fine-tuning, and one-GPU accelerate fine-tuning safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# StyleTTS2 training router

Use this sub-skill when the task is to choose or launch a StyleTTS2 training workflow from a source checkout: first-stage pretraining, second-stage joint training, fine-tuning from a LibriTTS-style checkpoint, or the one-GPU accelerate fine-tuning variant.

For data-list schemas, 24 kHz audio preparation, config-field edits, asset paths, and OOD text files, route to `../data-and-config/` first. For pretrained synthesis demos and voice-use guidance, route to `../inference/`.

## Start here

1. Identify the stage and config file with [references/training-workflows.md](references/training-workflows.md).
2. Build the launch command with the bundled safe helper [scripts/build_training_command.py](scripts/build_training_command.py), not by copying source training scripts:

   ```bash
   python scripts/build_training_command.py --repo-root /path/to/StyleTTS2 --stage first --config Configs/config.yml
   ```

   The helper defaults to dry-run: it prints the exact command, checks the checkout/config/assets lightly, and does not train, download models, or write checkpoints. Add `--run` only after the user explicitly wants to start training.
3. Before resuming or switching from first-stage to second-stage/fine-tuning, read [references/checkpoints-and-resume.md](references/checkpoints-and-resume.md).
4. For launch failures, CUDA/backend problems, OOM/NaN behavior, DDP warnings, WavLM cache, or missing dependencies, use [references/troubleshooting.md](references/troubleshooting.md).

## Stage routing

- First stage: `--stage first`; uses `accelerate launch` and writes periodic `epoch_1st_*.pth` plus the final `first_stage_path` under `log_dir`.
- Second stage: `--stage second`; use the plain Python DataParallel launcher because the repository documents DDP/accelerate as not working for this stage.
- Fine-tuning: `--stage finetune`; starts from a second-stage pretrained checkpoint such as a LibriTTS checkpoint and new speaker data.
- One-GPU fine-tuning: `--stage finetune-accelerate`; emits the documented memory-saving accelerate command with `--mixed_precision fp16 --num_processes 1` by default.

Always expect CUDA for truthful training behavior. The source checkout is not a pip-installable package; activate an environment that can import the checkout modules, has CUDA-enabled PyTorch, and includes the runtime dependencies noted in the troubleshooting reference.
