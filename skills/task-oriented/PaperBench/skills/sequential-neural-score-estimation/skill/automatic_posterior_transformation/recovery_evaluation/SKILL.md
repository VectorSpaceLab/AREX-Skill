---
name: recovery_evaluation
description: Evaluate soft-mode APT recovery records for source-boundary, metric, and mechanism-faithfulness checks.
---

# Recovery Evaluation

Use this skill after a recovery harness has produced `recovery_result.json`. It is especially useful for soft-mode APT runs where the selected target is reduced or proxy rather than a full benchmark reproduction.

## Inputs
- Recovery result JSON with `metrics`, `paper_target`, and `mechanism_checks`.
- Experiment validation JSON from the recovery gate.
- Generated skill invocation log.

## Outputs
- Boolean checks for numeric metric, target consistency, gate pass, optimizer execution, and mechanism coverage.
- A concise recommendation of `accept` or `refine` for the analysis phase.

## Workflow
1. Verify that the recovery gate reports `ok: true`.
2. Confirm the configured metric is present and numeric.
3. Require mechanism flags for proposal correction, atomic loss, sequential update, generated skill invocation, and reduced optimizer execution when proxy mode is used.
4. Return actionable missing-check feedback rather than silently accepting a high scalar metric.

## Validation
Run `python scripts/evaluate_recovery_record.py --self-test`.

## Limitations
This skill complements but does not replace the Distiller recovery validator or final analysis report.
