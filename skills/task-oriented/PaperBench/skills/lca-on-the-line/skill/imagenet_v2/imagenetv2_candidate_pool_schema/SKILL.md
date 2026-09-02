---
name: imagenetv2_candidate_pool_schema
description: Validate and normalize ImageNetV2-style candidate pools with class labels, MTurk selection frequencies, and ranked model predictions.
---

# ImageNetV2 Candidate Pool Schema

Use this skill when a recovery or dataset-building task needs an auditable ImageNetV2-style candidate pool. Do not use it to sample final datasets or score model accuracy; those are downstream skills.

## Inputs
- JSON list of candidate records.
- Each record must include `candidate_id`, `class_id`, `label`, `selection_frequency`, and `predictions`.

## Outputs
- Normalized records sorted by `class_id` and `candidate_id`.
- Validation errors for missing fields, invalid frequencies, or malformed predictions.

## Workflow
1. Load candidate records from JSON.
2. Validate required fields and types.
3. Enforce `selection_frequency` in `[0, 1]`.
4. Normalize labels and prediction ids to strings.
5. Save normalized records for sampling and evaluation.

## Validation
Run `python scripts/candidate_pool.py tests/fixtures/candidates.json --output /tmp/normalized_candidates.json`.

## Limitations
This skill validates metadata and predictions only; it does not verify real image pixels or run MTurk.
