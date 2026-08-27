---
name: cli-workflows
description: "Generate safe, correct train.py, validate.py, inference.py, and
  torchrun/distributed commands for timm reference scripts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# timm CLI Workflows

Use this sub-skill when the user needs commands for timm's repository-root training, validation, or inference scripts, or when adapting examples into reproducible shell commands. Keep this focused on command construction and operational caveats; route API-level model/data/training internals to the model-library, data, or training sub-skills, and route benchmark/result-table analysis to benchmarking-and-results.

## Routing Checklist

- Use `references/train-validate-inference.md` for command shapes, dataset layout expectations, config files, output flags, CPU/debug variants, pretrained/checkpoint behavior, and NaFlex flags.
- Use `references/distributed-training.md` for `torchrun`, `distributed_train.sh` equivalence, DDP environment assumptions, local rank handling, and multi-GPU command patterns.
- Use `references/troubleshooting.md` when a command fails because scripts are missing, the dataset split path is wrong, CUDA is selected on a CPU host, downloads fail, result/class-map files fail, DDP hangs, NaFlex flags mismatch the model, or validation OOMs.
- Use `scripts/timm_cli_command_builder.py` to print dry commands without importing timm, running training, or checking local files.

## High-Value Defaults

- Prefer explicit `--data-dir`, `--model`, `--batch-size`, `--workers`, and `--device` rather than relying on script defaults.
- For CPU/debug commands, set `--device cpu`, small `--batch-size`, low `--workers`, and short training controls such as `--epochs 1`, `--val-interval 1`, or `--no-aug` via extra args.
- For CUDA commands, add `--amp` only when the target host has a supported accelerator and the requested dtype is valid for the workflow.
- For training datasets, point `--data-dir` at the base folder containing train and validation splits; for validation/inference, point it at the validation/image split folder unless a non-ImageFolder dataset string changes split handling.
- If the user installed timm from pip only, explain that the root scripts may not be installed; they need a checkout copy of `train.py`, `validate.py`, `inference.py`, or equivalent copied scripts.

## Bundled Command Builder

```bash
python scripts/timm_cli_command_builder.py train \
  --data-dir /data/imagenet --model resnet50 --batch-size 32 --device cpu \
  -- --epochs 1 --no-aug
```

The builder prints a shell-quoted command. It is intentionally dry: it never imports timm, never validates model names, never probes devices, and never opens datasets. Put advanced script flags after `--`, or pass repeated `--extra-arg=value` tokens when a wrapper cannot use passthrough arguments.
