---
name: cad_recovery_evaluation
description: Evaluate CAD conflict-recovery runs with exact-match metrics and mechanism-check summaries.
---

# CAD Recovery Evaluation

Use this skill when assessing whether a CAD experiment followed supplied context rather than a memorized prior in QA-style conflict items.

## Inputs
- Items containing `id`, `context_answer`, and `prior_answer`.
- Regular decoding predictions.
- CAD predictions.
- Per-item traces showing prompt separation, dual logits, logit adjustment, and token selection.

## Outputs
Exact-match metrics, improvement, per-item records, and mechanism-check booleans suitable for `recovery_result.json`.

## Workflow
1. Normalize answers by lowercasing and stripping whitespace/punctuation.
2. Score regular and CAD predictions against the context answer.
3. Verify every item has prompt separation, dual logits, adjusted logits, and selection trace.
4. Return metric and mechanism summaries.

## Validation
Run `tests/test_recovery_evaluation.py` or Distiller validation.

## Limitations
This evaluator is for reduced conflict QA recovery, not ROUGE or factuality metrics on summarization.
