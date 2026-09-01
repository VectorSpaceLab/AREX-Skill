---
name: posterior_sampling_baseline
description: Generate deterministic reference and approximate posterior samples for bounded simulation-based inference recovery experiments.
---

# Posterior Sampling Baseline

Use this skill when an SBI benchmark recovery needs posterior samples to feed into distributional metrics. It consumes a task item from `sbibm_task_protocol` and emits reference and approximate sample matrices.

## Inputs
- Task item JSON containing analytic posterior mean and variance.
- Number of samples, random seed, and approximation mode: `matched`, `shifted`, or `wide`.

## Outputs
- JSON sample file containing reference samples, approximate samples, and sampling metadata.

## Workflow
1. Read the task item and validate posterior parameters.
2. Draw reference samples from the analytic posterior.
3. Draw approximate samples from the selected approximation distribution.
4. Record sample count, dimension, seed, and approximation mode.

## Validation
Run the included tests or `validate_skill_tree.py --run-tests`.

## Limitations
The module is a reduced posterior-sampling baseline, not a full neural SBI algorithm. It is valid for soft-mode proxy recovery when the goal is to exercise the benchmark comparison mechanism.
