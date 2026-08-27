---
name: cli-and-operations
description: "Guides agents using Axolotl CLI commands, launcher flags,
  agent-docs, config-schema, install checks, merge LoRA, inference, vLLM
  serving, evaluation, fetch, and quantize operations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI and Operations

Use this sub-skill when the task is about an `axolotl` command, CLI flags, command construction, `agent-docs`, `config-schema`, install checks, fetching examples, preprocessing runs, training launchers, inference, evaluation, LoRA merge, sharded FSDP merge, vLLM serving, cloud invocation, or post-training quantization.

## Read First

- [references/cli-reference.md](references/cli-reference.md) for the command map, launcher argument placement, option syntax, and `agent-docs`/`config-schema` usage.
- [references/operations.md](references/operations.md) for safe operational sequences from install checks through preprocess, train, evaluate, inference, merge, vLLM serve, fetch, and quantize.
- [references/troubleshooting.md](references/troubleshooting.md) for symptom-driven fixes around missing entry points, broken imports, config paths, overrides, launcher args, chat/Gradio conflicts, adapter paths, vLLM, and cloud configs.
- [scripts/axolotl_command_builder.py](scripts/axolotl_command_builder.py) to build a safely quoted Axolotl command from a config path, command name, launcher, and JSON options without executing it.
- [scripts/check_axolotl_install.py](scripts/check_axolotl_install.py) to check package metadata, top-level import, `axolotl` on `PATH`, and `axolotl --help` without starting training or loading a model.

## Fast Workflow

1. Check the local install first when the task mentions `command not found`, import errors, or a failing help/schema command.
2. Use `axolotl agent-docs --list`, `axolotl agent-docs <topic>`, and `axolotl config-schema --field <name>` for installed-package truth before guessing config keys.
3. Build commands with config path first, Axolotl overrides before the `--` separator, and launcher-specific args after `--`.
4. Prefer `axolotl preprocess config.yml --debug` before long training when dataset formatting, `chat_template`, labels, packing, or tokenization is uncertain.
5. Route field-level YAML, dataset, method, model, adapter, DeepSpeed, FSDP, or performance tuning questions to the matching sibling sub-skill after the command route is clear.

## Boundaries

This sub-skill owns Axolotl CLI entry points, safe command construction, install/entry-point checks, operational sequencing, `fetch`, `agent-docs`, `config-schema`, cloud flags, inference/evaluation/merge/vLLM/quantize command routes, and common CLI failures. Route detailed config fields and dataset shapes to `data-and-configs`, method recipes to SFT/pretraining or RL/preference sub-skills, model/adapters to `model-loading-and-adapters`, and distributed/performance backend tuning to `distributed-and-performance`.
