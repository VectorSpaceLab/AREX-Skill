---
name: proxy_recovery_evaluation
description: Decide whether a declared soft-mode proxy exercises the Accuracy on the Line mechanism.
---

# Proxy Recovery Evaluation

Use this skill after a recovery harness has produced calibration metrics. It evaluates whether a reduced or proxy experiment is acceptable evidence under soft mode. Do not use it to fabricate metrics; it consumes executable experiment outputs.

## Inputs

- A calibration result with `pearson_r`, slope/intercept, and residuals.
- A declared target threshold, usually from `module_plan.json.fast_recovery_target.paper_value`.
- Mechanism checks covering paired records, line fitting, residual inspection, source boundary, and proxy declaration.

## Outputs

- `accepted_proxy`, `metric_gap`, `mechanism_ok`, and human-readable reasons.
- A compact JSON decision that analysis can inspect.

## Workflow

1. Confirm the recovery is explicitly declared as proxy evidence.
2. Check that all required mechanism booleans are true.
3. Compare the observed Pearson correlation against the declared threshold.
4. Report metric gap and reasons without upgrading proxy evidence to full reproduction.

## Validation

Run the included tests or call `python scripts/evaluate_proxy.py --calibration <file> --checks <file> --threshold 0.95`.

## Limitations

This skill accepts soft-mode proxy evidence only. Hard-mode runs or full benchmark claims require real benchmark results rather than this reduced decision.
