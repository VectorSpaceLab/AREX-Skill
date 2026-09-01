---
name: imagenetv2_selection_frequency_sampling
description: Sample class-balanced ImageNetV2 proxy datasets using MatchedFrequency, Threshold0.7, or TopImages selection-frequency strategies.
---

# ImageNetV2 Selection Frequency Sampling

Use this skill after candidate records have been validated. It implements the paper's key sampling ablation: final ImageNetV2 variants differ by how candidate MTurk selection frequencies are used.

## Inputs
- Normalized candidate JSON from `imagenetv2_candidate_pool_schema` or an equivalent list.
- Strategy: `matched_frequency`, `threshold_0_7`, or `top_images`.
- Per-class sample count.

## Outputs
- Sampled records.
- Strategy statistics including class coverage and average selection frequency.

## Workflow
1. Group candidates by class.
2. For `top_images`, choose highest selection frequencies with id tie-breaks.
3. For `threshold_0_7`, filter to frequency at least 0.7, then choose highest frequencies.
4. For `matched_frequency`, sort by distance to target frequency bins derived from the class pool quantiles.
5. Emit deterministic samples and warnings for underfilled classes.

## Validation
Run `python scripts/sample_by_frequency.py tests/fixtures/normalized.json --strategy top_images --per-class 1 --output /tmp/sample.json`.

## Limitations
This skill samples metadata records; it does not fetch images or collect MTurk annotations.
