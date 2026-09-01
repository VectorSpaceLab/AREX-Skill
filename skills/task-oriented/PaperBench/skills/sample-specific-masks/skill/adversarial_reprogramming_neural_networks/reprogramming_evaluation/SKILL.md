---
name: reprogramming_evaluation
description: Validate mechanism evidence for adversarial reprogramming proxy or full recovery experiments.
---

# Mechanism-Faithful Reprogramming Evaluation

Use this skill after a recovery run to check whether it exercised the paper mechanism: frozen target model, universal input program, output remapping, optimizer update, numeric metric, and clean source boundary. Do not accept a high metric if these mechanism checks are missing.

## Inputs
- Recovery result dictionary.
- Training trace dictionary.
- Optional source manifest paths.

## Outputs
- `ok` boolean.
- List of errors.
- Metric and mechanism summary.

## Workflow
1. Verify at least one numeric metric.
2. Verify required mechanism booleans.
3. For reduced/proxy recovery, verify parameter change and loss fields.
4. Verify forbidden original repository paths are absent from the source manifest.

## Validation
Run `python tests/test_reprogramming_evaluation.py`.

## Limitations
This helper evaluates artifact consistency. It does not independently re-run the recovery experiment.
