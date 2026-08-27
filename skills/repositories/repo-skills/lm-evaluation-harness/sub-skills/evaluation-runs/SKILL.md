---
name: evaluation-runs
description: "Run lm-evaluation-harness evaluations through the lm-eval CLI,
  YAML configs, and Python APIs with safe flags for outputs, caching, chat
  templates, seeds, limits, unsafe-code confirmation, and debugging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Evaluation Runs

Use this sub-skill when a future agent needs to execute, debug, or programmatically assemble an `lm-eval` evaluation run. It covers `lm-eval run`, config-backed runs, and Python calls to `simple_evaluate()` / `EvaluatorConfig`.

## Start Here

1. Confirm the command surface with the bundled checker:
   ```bash
   python scripts/check_lm_eval_cli.py --json
   ```
2. Choose the run style:
   - CLI flags for quick one-off runs.
   - YAML config for reproducible runs or long argument sets.
   - Python API for pipelines that need to inspect or reuse result dictionaries.
3. Build a dry command/config before running expensive model inference:
   ```bash
   python scripts/build_eval_command.py \
     --model hf --model-arg pretrained=gpt2 --tasks hellaswag,arc_easy \
     --limit 5 --output-path results/gpt2-smoke --log-samples \
     --cache-requests true --use-cache cache/gpt2_eval
   ```
4. Run validation/listing only as needed:
   - `lm-eval ls tasks` to find registered task names.
   - `lm-eval validate --tasks hellaswag,arc_easy` before longer runs.
   - `lm-eval run --config eval.yaml` for the actual evaluation.

## Route To References

- [CLI reference](references/cli-reference.md): command shapes, flag choices, config-vs-CLI precedence, debugging flags, and dry-run examples.
- [Configuration](references/configuration.md): YAML schema, reproducible config patterns, and how CLI overrides merge with config files.
- [Python API](references/python-api.md): `simple_evaluate()`, `EvaluatorConfig`, `TaskManager`, seeds, cache flags, and result dictionary handling.
- [Troubleshooting](references/troubleshooting.md): missing tasks, `samples` vs `limit`, `log_samples` output requirements, chat-template pitfalls, cache refresh/delete, unsafe code confirmation, and optional backend errors.

## Bundled Scripts

- [`scripts/build_eval_command.py`](scripts/build_eval_command.py) builds safe `lm-eval run` command lines and optional YAML config files without importing model backends or downloading weights.
- [`scripts/check_lm_eval_cli.py`](scripts/check_lm_eval_cli.py) checks importability and CLI help surfaces for `lm-eval`, `lm_eval`, `run`, `ls`, and `validate`.

## Boundaries

- For model backend installation, `--model_args` details, device/backend caveats, and registry selection, route to `../model-backends/`.
- For writing new task YAMLs, custom metrics, prompt templates, and task validation depth, route to `../task-authoring/`.
- For result schemas, sample files, W&B/HF Hub logging analysis, and postprocessing, route to `../result-logging/`.
- For decontamination or benchmark maintenance workflows, route to `../decontamination-maintenance/`.
