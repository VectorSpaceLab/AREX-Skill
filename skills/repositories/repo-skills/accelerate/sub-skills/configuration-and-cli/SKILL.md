---
name: configuration-and-cli
description: "Use this sub-skill when working with Hugging Face Accelerate
  configuration files and CLI commands, including accelerate
  config/default/update/env/launch/test/estimate-memory/merge-weights/to-fsdp2,
  launch command construction, multi-node and SLURM planning, config validation,
  and CLI troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Accelerate Configuration and CLI

Use this sub-skill to create, validate, update, and reason about Accelerate config files and command-line invocations.

## When to Use

- Build or debug `accelerate launch` commands for scripts, modules, non-Python executables, multi-node jobs, or SLURM wrappers.
- Create or adapt `default_config.yaml` or custom `--config_file` YAML for local CPU, single accelerator, multi-GPU, multi-XPU, or multi-node runs.
- Explain or safely run `accelerate config`, `config default`, `config update`, `env`, `test`, `estimate-memory`, `merge-weights`, or `to-fsdp2`.
- Diagnose missing configs, invalid YAML, unknown keys, conflicting launcher flags, rendezvous mistakes, subprocess tracebacks, and training-script argument separation.

## Routing Boundaries

- For training-loop code changes such as `Accelerator.prepare`, dataloaders, gradient accumulation, trackers, and checkpoint hooks, use `../training-loop-integration/`.
- For DeepSpeed, FSDP, Megatron-LM, TPU, and backend-specific semantics beyond CLI flag placement, use `../distributed-training-backends/`.
- For `estimate-memory` interpretation and big-model device-map loading workflows, use `../big-model-inference/`.

## Start Here

1. Read `references/cli-reference.md` for command inventory, safe command patterns, and which commands mutate files.
2. Read `references/configuration.md` before editing YAML or choosing top-level config keys.
3. Read `references/launching.md` before composing `accelerate launch`, multi-node, module, no-Python, or SLURM commands.
4. Read `references/troubleshooting.md` when a config or launch command fails.

## Bundled Helpers

- `scripts/validate_accelerate_config.py`: validates YAML syntax, known top-level keys, required fields, and common local/multi-node conflicts without importing Accelerate.
- `scripts/print_accelerate_help_summary.py`: invokes installed `accelerate --help` subcommands when available and prints a compact availability summary.

Run helpers with `python path/to/script.py --help` for usage.
