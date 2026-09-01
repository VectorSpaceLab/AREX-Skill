---
name: training_dynamics_scoring
description: Convert per-example training dynamics into CCS-compatible importance scores for coreset selection.
---

# Training Dynamics Scoring

Use this skill when a coreset workflow needs deterministic per-example importance scores derived from model training dynamics. It is appropriate for Coverage-centric Coreset Selection style experiments and for reduced proxy recovery where probability traces are synthetic but still aligned to labels and indices.

Do not use this skill to choose the coreset directly or to claim full model accuracy. It only converts logged probabilities into scores that downstream selection modules consume.

## Inputs

- Records with `index`, `epoch`, `probabilities`, and `label` fields.
- `num_classes`, inferred from probabilities when omitted.
- Optional `max_el2n_epoch`, matching the paper-style early dynamics window.

## Outputs

- `targets`: label per original index.
- `correctness`, `forgetting`, and `last_correctness` counts.
- `accumulated_margin`: target probability minus best non-target probability summed across records.
- `el2n`: Euclidean distance between one-hot label and probabilities over the configured early window.
- Optional `entropy` and `loss` when final probabilities are available.

## Workflow

1. Validate that every probability vector is non-empty and matches the class count.
2. Sort records by epoch while preserving original index identities.
3. Update correctness and forgetting whenever an example changes from correct to incorrect.
4. Add accumulated margins for every record and EL2N contributions before the configured cutoff.
5. Return plain Python lists so later scripts can serialize the result without torch or numpy.

## Validation

Run `python tests/test_training_dynamics_scoring.py` or validate the skill tree with the Distiller validator using `--run-tests`.

## Limitations

This skill intentionally avoids framework-specific tensors. Full-paper score generation can wrap it after extracting probabilities from PyTorch logs, but the reusable contract is standard-library only.
