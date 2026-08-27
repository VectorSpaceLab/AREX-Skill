---
name: cli-workflows
description: "Use the Unsloth Typer CLI for training, inference, chat, export,
  Studio, connect, dry-run config validation, pass-through flags, and parser
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Unsloth CLI Workflows

Use this sub-skill when the user wants command-line Unsloth workflows instead of direct Python APIs: `unsloth train`, `inference`, `chat`, `export`, `list-checkpoints`, `studio`, `run`, or `connect`.

## Route first

- Use `unsloth train --dry-run` before any expensive training to validate config resolution without model or dataset downloads.
- Route direct Python API code, trainer internals, and notebook-style finetuning to `../core-training/SKILL.md`.
- Route export backend behavior, format tradeoffs, and checkpoint conversion details to `../model-export/SKILL.md`.
- Route Studio backend/API internals and server implementation work to `../studio-runtime/SKILL.md`.

## Read or run

- Read `references/cli-reference.md` for the command catalog, safe command examples, Studio `run` alias behavior, connect targets, and pass-through rules.
- Read `references/configuration.md` for the YAML/JSON config schema, CLI override mapping, token precedence, and dry-run workflow.
- Read `references/troubleshooting.md` when diagnosing parser errors, missing config/model/dataset inputs, System32 guard failures, Studio exposure flags, connect side effects, or alias conflicts.
- Run `scripts/unsloth_cli_smoke.py --help` to see the safe smoke checker; run it against an installed `unsloth` CLI to validate help output and `train --dry-run` without downloads.
- Copy or adapt `scripts/training_config_template.yaml` as a starter config, then replace placeholder model/dataset/output values before a real training run.

## Safe default workflow

1. Convert the user request into `scripts/training_config_template.yaml`-style YAML with explicit `model`, one dataset source, `training.training_type`, and output settings.
2. Run `unsloth train --config config.yaml --dry-run` and inspect the resolved YAML before starting training.
3. For one-shot inference or chat, prefer `unsloth inference <model> <prompt>` or `unsloth chat <model>`; add `--no-server` if a running Studio server should not be reused.
4. For a local Studio API server with a loaded model, use `unsloth run --model <model-or-gguf-repo>` or `unsloth studio run --model <model-or-gguf-repo>`; both use the same implementation.
5. For agent integration, start Studio first, then use `unsloth connect <agent> --model <model> --no-launch` to review environment/config changes before launching an agent.
