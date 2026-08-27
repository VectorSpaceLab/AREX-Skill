---
name: "x-transformers"
description: "Route x-transformers transformer construction, sequence wrappers,
  and recipe workflows through self-contained sub-skills."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# x-transformers

Use this skill when the user asks about the x-transformers package, its transformer constructors, wrapper APIs, vision wrapper, or the repository's training recipes.

## Quick start

- For a safe installation check, read [installation](references/installation.md).
- For a fast runtime smoke, run `scripts/probe_backend.py` and `scripts/smoke_models.py`.
- For exact constructor and wrapper signatures, read [API reference](references/api-reference.md).
- For feature-selection and compatibility questions, read [compatibility](references/compatibility.md) and the relevant sub-skill reference.
- For task-specific failures, read [troubleshooting](references/troubleshooting.md).

## Choose a route

### `core-models`
Use this when the request is about building or tuning the base transformer stack: `TransformerWrapper`, `XTransformer`, `ViTransformerWrapper`, `AttentionLayers`, `Attention`, `Encoder`, `Decoder`, `PrefixDecoder`, `CrossAttender`, `AttentionPool`, and `TransformerBlock`.

Typical triggers:
- choosing attention flags or positional families
- debugging shape or mask errors in a constructor
- building text, seq2seq, or vision-wrapper models from scratch

### `sequence-workflows`
Use this when the request is about wrapper and specialized-model workflows: autoregressive generation, continuous sequences, xVal mixed inputs, XL recurrence, belief-state or next-latent objectives, DPO, FreeTransformer, GPTVAE, NeoMLP, entropy tokenization, or XMLatentDecoder flows.

Typical triggers:
- generation and sampling APIs
- continuous or mixed discrete/continuous sequences
- latent or preference objectives
- memory or test-time-training wrappers

### `training-recipes`
Use this when the request is about the repository's `train_*.py` examples, enwik8 data assumptions, or a safe smoke for recipe-style training.

Typical triggers:
- understanding which training script to run
- checking required extras and data files
- adapting a recipe to a smaller or safer smoke

## Route selection rules

1. If the task names a base constructor, attention flag, positional family, pooling mode, or vision wrapper, start with `core-models`.
2. If the task names a wrapper, generation method, continuous/xVal/memory/latent objective, or preference objective, start with `sequence-workflows`.
3. If the task names a `train_*.py` script or enwik8 recipe, start with `training-recipes`.
4. If the task is only about install/import/runtime identity, begin with `references/installation.md` and `scripts/probe_backend.py`.

## Notes for future agents

- The package has no dedicated end-user CLI entry point; most workflows are Python APIs or example scripts.
- Keep runtime instructions self-contained inside this skill tree.
- If you need a quick end-to-end smoke, prefer `scripts/smoke_models.py` or the copy-task smoke under `sub-skills/training-recipes/scripts/` rather than the long native recipes.
