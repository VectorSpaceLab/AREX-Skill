---
name: multitask_mixture_split
description: Construct prompted multitask training mixtures while enforcing held-out dataset boundaries for zero-shot evaluation.
---

# Multitask Mixture and Held-Out Split

Use this skill after prompt rendering when you need an auditable P3/T0-style source-task mixture and held-out evaluation set. Do not use it to render templates or train a model.

## Inputs
- Rendered prompted records with dataset, task family, template, source, and target metadata.
- A list of held-out dataset ids or task families.

## Outputs
- `train`, `eval`, and `diagnostics` dictionaries showing record counts and template coverage.

## Workflow
1. Partition records by dataset id and optional held-out task family.
2. Ensure no held-out dataset id appears in the training split.
3. Count templates per dataset to document prompt diversity.
4. Return JSON-serializable diagnostics for source-boundary review.

## Validation
Run the included tests or Distiller skill validation with `--run-tests`.

## Limitations
The skill implements deterministic split construction, not large-scale sampling weights from the full T0 training pipeline.
