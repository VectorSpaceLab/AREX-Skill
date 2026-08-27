---
name: configuration-ui
description: "Guide JSON config editing, smoke configs, CLI override precedence,
  stage command construction, metrics JSONL inspection, and the Streamlit
  control panel/job manager."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# configuration-ui

Use this sub-skill when a future Researcher needs to edit or inspect this repo's
JSON stage configs, build safe training/UI command lines, use smoke configs,
inspect metrics JSONL, or operate the Streamlit control panel.

## Read first

- For config precedence, dataclass fields, smoke/full JSON behavior, and CLI
  override rules, read [references/configuration.md](references/configuration.md).
- For Streamlit pages, job registry behavior, GPU-busy guarding, logs, and UI
  metrics, read [references/control-panel-ui.md](references/control-panel-ui.md).
- For common config/UI/metrics failures, read
  [references/troubleshooting.md](references/troubleshooting.md).

## Safe bundled helpers

- [scripts/print_config_summary.py](scripts/print_config_summary.py) summarizes
  one or more JSON config files and compares explicit keys against a base JSON
  without importing the repo.
- [scripts/inspect_metrics_jsonl.py](scripts/inspect_metrics_jsonl.py)
  summarizes metrics JSONL columns, last row, numeric ranges, and
  malformed-line counts without pandas or repo imports.

Both helpers are read-only by default, have `--help`, and include `--demo` tiny
fixture modes.

## Route elsewhere

- Algorithm choices, loss interpretation, RLHF stage sequencing, KL/reward
  tuning, and training-stage failure analysis: use
  [../post-training-rlhf/SKILL.md](../post-training-rlhf/SKILL.md).
- Base architecture, legacy pretraining, DDP/bf16 pretraining, checkpoint
  structure, and memory planning: use
  [../model-pretraining/SKILL.md](../model-pretraining/SKILL.md).
- Dataset schemas, packed HDF5 validation, preference JSONL validation, and RL
  prompt validation: use [../data-preparation/SKILL.md](../data-preparation/SKILL.md).
- GSM8K evaluation details, direct chat/raw inference, checkpoint loading, and
  sampling controls: use [../evaluation-chat/SKILL.md](../evaluation-chat/SKILL.md).

## Operating guardrails

- Prefer `configs/smoke/*.json` for command/config smoke checks; those use a
  sibling `configs/smoke/base.json` and are CPU-oriented.
- Use `--print-config` before launching long jobs when changing JSON or CLI
  overrides.
- Treat UI launches as process-spawning operations: check the UI job registry
  status and the GPU-busy guard before starting GPU jobs.
- Treat Weights & Biases as optional. The repo always writes metrics JSONL under
  the configured log directory even when W&B is disabled or unavailable.
