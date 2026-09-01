---
name: upsampling_evaluation_protocol
description: Preserve guided diffusion target metadata, proxy declarations, classifier scale, and evaluation protocol consistency.
---

# Upsampling and Evaluation Protocol

Use this skill when preparing `recovery_result.json`, experiment plans, or validation checks for guided diffusion experiments. It keeps full and proxy targets aligned with the module plan and paper metrics.

## Inputs

- Dataset, split, metric, and paper target value.
- Resolution and optional upsampling stage.
- Sample count, classifier scale, and checkpoint or proxy declaration.
- Recovery mode: full, reduced, or proxy.

## Outputs

- Normalized protocol object.
- `ok` boolean plus warnings/errors.
- Target metadata suitable for `recovery_result.json.paper_target`.

## Workflow

1. Copy target metadata from `module_plan.json.fast_recovery_target` rather than inventing a new metric.
2. Require classifier scale for guided full or reduced sampling claims.
3. Distinguish base-resolution guided samples from cascaded upsampling results.
4. For proxy recovery, require `proxy: true`, rationale, metric name, and mechanism checks.
5. Reject metric or dataset drift during analysis.

## Validation

Run `python scripts/evaluation_protocol.py --mode proxy`. The tests verify that a proxy protocol passes with declared metadata and that full guided claims without classifier scale fail.

## Limitations

This skill does not compute FID or precision/recall. It validates evaluation metadata and prevents unsupported comparisons to the paper tables.
