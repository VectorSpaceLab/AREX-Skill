---
name: openclip_scale_protocol
description: Build and validate OpenCLIP-style scale tables for CLIP scaling-law experiments, including total compute and error metric derivation.
---

# OpenCLIP Scale Protocol

Use this skill when a recovery or analysis needs to represent CLIP scale points from the paper: dataset scale, model scale, samples seen, compute per sample, and downstream metrics.

## Inputs
- JSON list of records with `dataset`, `model`, `samples_seen`, `gmac_per_sample`, and optional `accuracy` or `recall_at_5` values.
- Metrics should be percentages, not fractions.

## Outputs
- JSON with validated records, `total_compute`, and derived error columns.

## Workflow
1. Validate positive `samples_seen` and `gmac_per_sample`.
2. Compute `total_compute = samples_seen * gmac_per_sample`.
3. Convert `accuracy` to `classification_error = 100 - accuracy`.
4. Convert `recall_at_5` to `retrieval_error = 100 - recall_at_5`.
5. Preserve raw records for downstream power-law fitting.

## Validation
Run `python tests/test_scale_protocol.py`.

## Limitations
This skill structures scale evidence; it does not train CLIP models or claim full LAION-scale reproduction.
