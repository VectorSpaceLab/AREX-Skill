---
name: open-alpha-tensor
description: "Guides OpenAlphaTensor training, configuration, checkpointing, and
  troubleshooting for matrix-multiplication search runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# OpenAlphaTensor

Use this sub-skill when the user wants to train OpenAlphaTensor, tune the JSON/CLI configuration, manage checkpoints, or understand the outputs written by the training pipeline.

## Triggers

- Run `python main.py` or call `train_alpha_tensor(...)`.
- Map `config.json` keys to the public API.
- Tune checkpoint, save, or output directories.
- Debug optimizer selection or device placement.

## Read next

- `references/api-reference.md` for the public training function and grouped parameters.
- `references/configuration.md` for JSON and CLI configuration keys.
- `references/workflows.md` for the training, checkpoint, and save flow.
- `references/troubleshooting.md` for long-run, path, and checkpoint recovery.
- `scripts/open_alpha_tensor_probe.py` for a safe signature and config-validation check.

## What to include

- The `train_alpha_tensor(...)` entry point.
- CLI-to-API mapping from `main.py`.
- JSON config defaults and runtime overrides.
- Checkpoint and save-directory behavior.
- Device and optimizer selection.

## What to exclude

- Long training runs by default.
- Generated data or artifact downloads.
- Source-repo path links in runtime guidance.

## Quick decision rule

If the user asks “how do I launch or tune OpenAlphaTensor?”, start here. If the request is only about the underlying matrix-search paper or benchmark results, use the references rather than the script.
