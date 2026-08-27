---
name: setup-and-command-building
description: "Guides OFA installation, environment checks, PYTHONPATH setup, and
  safe train/evaluate command construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# setup-and-command-building

Use this sub-skill when a user wants to install OFA, verify the environment, figure out `PYTHONPATH` or `--user-dir`, or turn a long distributed shell script into a copyable command.

## Trigger phrases

- "How do I run OFA?"
- "Why does `train.py` import fail?"
- "What `PYTHONPATH` do I need?"
- "Render the caption/VQA/RefCOCO/MMSpeech command for me."
- "Which ports, ranks, or GPUs should I use?"

## What this sub-skill owns

- repository installation and minimal verification,
- Fairseq fork visibility and import ordering,
- command shape for `train.py` and `evaluate.py`,
- distributed launch scaffolding and safe launch parameters,
- command rendering for the common OFA task families.

## What it excludes

- dataset schemas and row validation -> `data-formats`,
- task-specific workflows -> the dedicated workflow sub-skill,
- model/criterion internals -> `model-internals-and-extension`.

## Read these files

- [references/command-recipes.md](references/command-recipes.md) for copyable launch patterns and common flags.
- [references/troubleshooting.md](references/troubleshooting.md) for import, CUDA, and launch failures.
- [../../scripts/check_ofa_environment.py](../../scripts/check_ofa_environment.py) to confirm imports and CLI help.
- [../../scripts/render_ofa_command.py](../../scripts/render_ofa_command.py) to render a command without executing it.

## Typical workflow

1. Check the environment.
2. Confirm the repo root and bundled Fairseq fork are visible to Python.
3. Decide which task sub-skill owns the actual workflow.
4. Render the command with explicit data, checkpoint, and `selected_cols` values.
5. Only launch the heavy job after the relevant input validator passes.

## Notes

- Most OFA commands are Fairseq launches plus OFA-specific overrides.
- The command renderer is intentionally conservative; it does not guess dataset or checkpoint paths.
- Use CPU-only help checks only for import and parser validation. Do not treat them as proof of GPU readiness.
