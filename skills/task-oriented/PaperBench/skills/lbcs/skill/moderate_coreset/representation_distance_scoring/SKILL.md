---
name: representation_distance_scoring
description: Compute class-center representation distances for Moderate-DS style data selection from labeled feature records.
---

# Representation Distance Scoring

Use this skill when a recovery or application has labeled examples with numeric hidden representations and needs the Moderate-DS distance score. Do not use it to train a model, choose the coreset size, or evaluate downstream accuracy; those are separate modules.

## Inputs
- A JSON list of records with `id`, `label`, and `representation` fields.
- Numeric representation vectors must have consistent dimensionality.

## Outputs
- Class centers keyed by label.
- Per-record Euclidean distance scores from each representation to its own class center.

## Workflow
1. Validate record ids, labels, and representation dimensions.
2. Average representation vectors separately for every class label.
3. Compute the Euclidean norm between each record representation and the matching class center.
4. Return stable diagnostics that preserve the input ids and labels.

## Validation
Run `python scripts/score_representations.py --self-test` or `python -m pytest tests` when pytest is available. The deterministic tests cover centers, distances, and schema failures.

## Limitations
This skill assumes representations already exist. It intentionally does not read the original paper repository, access model internals, or perform data augmentation.
