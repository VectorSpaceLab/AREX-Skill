---
name: training-eval-cli
description: "Use this repo skill to build and troubleshoot Swin-Transformer
  supervised ImageNet training, fine-tuning, evaluation, throughput, DDP, AMP,
  and config override commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# training-eval-cli

Use this sub-skill when a task asks for supervised `main.py` workflows: training from scratch, evaluation, fine-tuning from pretrained weights, throughput measurement, command-line flags, distributed launchers, memory levers, or config overrides.

## Covers

- `main.py` train/eval/fine-tune/throughput workflow shape.
- `--cfg`, `--data-path`, `--zip`, `--cache-mode`, `--pretrained`, `--resume`, `--accumulation-steps`, `--use-checkpoint`, AMP and fused flags.
- `torchrun`/distributed-launch command templates and `LOCAL_RANK` behavior.
- Supervised config families under Swin V1, Swin V2, and Swin-MLP.
- Safe command validation without running training.

## Routes elsewhere

- Data root or checkpoint-schema diagnosis: `data-and-checkpoints`.
- Model constructor/API questions: `core-models`.
- SimMIM pretraining/fine-tuning: `simmim-workflows`.
- Swin-MoE/Tutel/fused CUDA extension: `moe-and-acceleration`.

## Workflow

1. Pick a config family using `../../references/model-zoo-and-configs.md`.
2. Validate data/checkpoint assumptions with `data-and-checkpoints`.
3. Compose a command using `../../scripts/swin_cli_command_builder.py` or the recipes in `references/supervised-workflows.md`.
4. Validate the command shape with `scripts/validate_swin_command.py --repo-root <checkout> -- <command>`. The validator never launches training.
5. If the command still fails, read `references/troubleshooting.md` for DDP, memory, config, AMP, and optional dependency issues.

## Safety warning

Actual `main.py` training/evaluation is GPU/data/checkpoint heavy. Do not run full native training as a quick check. Use CPU model construction and command validation first.

## Linked files

- `references/supervised-workflows.md` - recipes for train, eval, fine-tune, and throughput.
- `references/cli-reference.md` - flag meanings and config side effects.
- `references/troubleshooting.md` - launcher, memory, and flag mistakes.
- `scripts/validate_swin_command.py` - safe command-shape validator.
