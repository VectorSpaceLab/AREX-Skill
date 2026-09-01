---
name: baseline_path_protocol
description: Build and validate absence baselines and straight-line interpolation paths for Integrated Gradients recovery experiments.
---

# Baseline Path Protocol

Use this skill when an Integrated Gradients experiment needs a baseline and interpolation points. Do not use it to choose a task label, evaluate model quality, or replace the attribution computation itself.

## Inputs
- `input_vector`: numeric feature vector for the explained example.
- `baseline_vector`: same-length vector representing absence of signal.
- `steps`: positive integer Riemann step count.
- Optional `baseline_score` and `near_zero_tolerance` for baseline diagnostics.

## Outputs
- Ordered interpolation points for `alpha = 1/steps ... 1`.
- Baseline metadata with warnings when the baseline score is not near zero.

## Workflow
1. Check that the input and baseline vectors are non-empty and equal length.
2. Check that `steps` is positive.
3. Generate the straight-line path `baseline + alpha * (input - baseline)`.
4. Include the original input as the last point and omit alpha zero for Equation 3 style averaging.
5. Record baseline-score warnings without replacing the caller's baseline.

## Validation
Run `python tests/test_baseline_path.py` from this skill directory or validate through the Distiller skill-tree validator.

## Limitations
This skill does not compute gradients or decide whether a baseline is semantically perfect; it provides the auditable protocol and diagnostics required by the paper.
