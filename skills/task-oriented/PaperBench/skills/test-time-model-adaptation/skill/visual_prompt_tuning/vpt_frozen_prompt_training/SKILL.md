---
name: vpt_frozen_prompt_training
description: Configure and verify Visual Prompt Tuning trainability with frozen backbone and trainable prompt/head parameters.
---

# VPT Frozen Prompt Training

Use this skill when a VPT implementation or recovery harness needs to decide which parameters are trainable, compute tunable-parameter ratios, or verify that frozen backbone parameters did not change. Do not use this skill to insert prompt tokens or compute classification accuracy.

## Inputs

- Parameter records with `name`, `count`, and optional before/after scalar values.
- Role hints or naming conventions identifying prompt, classifier head, and backbone parameters.
- Optional optimizer settings for prompt/head groups.

## Outputs

- A trainability mask where prompt and head parameters are trainable and all backbone parameters are frozen.
- Optimizer parameter-group names containing no frozen backbone parameters.
- Tunable-count and tunable-percentage summaries.
- Freeze verification showing unchanged frozen parameters after a training step.

## Workflow

1. Classify each parameter by explicit role or by conservative name matching.
2. Mark only prompt and classifier-head roles as trainable.
3. Treat ambiguous Transformer, patch, attention, MLP, norm, and position parameters as frozen.
4. Build optimizer groups from the trainable subset.
5. Compute tunable percentage against total and frozen-backbone counts.
6. Compare before/after values to prove frozen parameters did not mutate.

## Validation

Run `python tests/test_training_config.py`, or use the Distiller validator with `--run-tests`.

## Limitations

This skill validates trainability semantics and parameter accounting. It does not implement a full deep-learning framework optimizer.
