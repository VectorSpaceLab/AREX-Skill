# Axolotl CLI Reference

Axolotl exposes one console script: `axolotl`. The current Click CLI expects commands in the form:

```bash
axolotl <command> [config.yml] [options]
```

The config can be a local YAML path or, for commands that load configs through Axolotl's config loader, a raw YAML URL. Click validates local config paths for most top-level commands before any model or dataset code runs.

## Command Map

| Command | Use | Notes |
| --- | --- | --- |
| `axolotl fetch examples` | Download example YAML configs | Networked helper; optional `--dest DIR`. |
| `axolotl fetch deepspeed_configs` | Download DeepSpeed JSON configs | Useful before DeepSpeed training configs. |
| `axolotl fetch docs` | Download docs for pip-only `agent-docs` fallback | Use when `agent-docs` cannot find bundled/repo docs. |
| `axolotl preprocess CONFIG` | Tokenize and validate datasets before training | Add `--debug` and `--debug-num-examples N` to inspect samples. |
| `axolotl train CONFIG` | Train or fine-tune from YAML | Default launcher is `accelerate`; supports `--launcher accelerate|torchrun|python`, `--cloud`, and `--sweep`. |
| `axolotl evaluate CONFIG` | Evaluate train/eval datasets through Axolotl | Supports the same launcher separator pattern as train. |
| `axolotl lm-eval CONFIG` | Run LM Evaluation Harness tasks from YAML | Supports `--cloud`; uses `lm_eval_*` fields in the config. |
| `axolotl inference CONFIG` | Run text inference | Supports launcher selection, `--chat`, `--gradio`, and model/adapter overrides. |
| `axolotl merge-lora CONFIG` | Merge LoRA/QLoRA adapters into a base model | Direct command, not launcher-wrapped. Often uses `--lora-model-dir`. |
| `axolotl merge-sharded-fsdp-weights CONFIG` | Combine sharded FSDP checkpoints | Supports `--launcher accelerate|torchrun|python`. |
| `axolotl vllm-serve CONFIG` | Start a vLLM server for online RL generation | Reads `base_model` plus `vllm:` settings; optional CLI overrides for host, port, tensor parallelism, dtype, and serve module. |
| `axolotl quantize CONFIG` | Post-training quantize a model via torchao | Requires `qat:` or `quantization:` settings; saves under the configured output directory. |
| `axolotl agent-docs [TOPIC]` | Print agent-oriented docs | Topics include `sft`, `grpo`, `preference_tuning`, `reward_modelling`, `pretraining`, `model_architectures`, and `new_model_support`. |
| `axolotl config-schema` | Dump the config schema | Use `--format yaml` or `--field FIELD` for focused inspection. |

## Option Syntax

Use dash-case for Click CLI overrides:

```bash
axolotl train config.yml --learning-rate 1e-4 --micro-batch-size 2
axolotl inference config.yml --lora-model-dir ./outputs/lora-out
```

Nested Pydantic config options use dot notation and dash-case for the CLI name, such as `--trl.beta 0.1`. Internal kwargs use underscores only inside Axolotl; future agents should prefer the public dash-case CLI.

Legacy module invocations still exist, but they use underscore-style options in many examples:

```bash
accelerate launch -m axolotl.cli.inference config.yml --lora_model_dir ./outputs/lora-out
```

Use the modern `axolotl <command>` form unless a user is explicitly debugging the legacy module path.

## Launcher Argument Placement

`train`, `evaluate`, `inference`, and `merge-sharded-fsdp-weights` accept `--launcher accelerate|torchrun|python`.

- `accelerate` becomes `accelerate launch ... -m axolotl.cli.<module> CONFIG`.
- `torchrun` becomes `torchrun ... -m axolotl.cli.<module> CONFIG`.
- `python` calls Axolotl's Python handler directly and does not use extra launcher args.
- Args after the standalone `--` are passed to the launcher, not to Axolotl.
- Axolotl config overrides belong before the standalone `--`.

Correct examples:

```bash
axolotl train config.yml --launcher torchrun --learning-rate 2e-4 -- --nproc_per_node=8
axolotl train config.yml --launcher accelerate -- --config_file=accelerate_config.yml --num_processes=4
axolotl evaluate config.yml --launcher torchrun -- --nproc_per_node=2
axolotl inference config.yml --launcher accelerate --chat -- --num_processes=2
```

When users report that overrides are ignored, check for options placed after `--`; launcher arguments are not parsed as Axolotl config overrides.

## Schema and Agent Docs

Use installed-package introspection before inventing field names:

```bash
axolotl agent-docs --list
axolotl agent-docs grpo
axolotl config-schema --field adapter
axolotl config-schema --format yaml
```

If `agent-docs` reports missing docs in a pip-only install, run `axolotl fetch docs` in the working directory or use the public docs. If `config-schema --field FIELD` fails with `Unknown field`, omit `--field` and inspect the top-level properties.

## Safe Command Builder

Use the bundled helper to construct commands without shell-quoting mistakes or execution:

```bash
python scripts/axolotl_command_builder.py config.yml --command train --launcher torchrun \
  --options-json '{"learning_rate": "2e-4", "micro_batch_size": 4}' \
  --launcher-args-json '["--nproc_per_node=8"]'
```

The helper prints both an argv JSON array and a safely quoted shell string. It validates command names, config existence by default, launcher support, JSON shape, and command-specific flag conflicts such as `--chat` with `--gradio`.
