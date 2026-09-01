---
name: posterior_predictive_validation
description: Validate SNPE-style posterior recovery using parameter correlation, posterior predictive summary error, and mechanism checks.
---

# Posterior Predictive Validation

Use this skill to decide whether a reduced or full simulation-based posterior recovery has exercised the paper mechanism. Do not accept proxy recovery from a metric alone; require mechanism checks.

## Inputs
- Posterior mean or posterior samples.
- True parameter if using synthetic data.
- Observed summary and posterior predictive summaries.
- Declared metric threshold and mechanism flags.

## Outputs
- Filter correlation metric.
- Posterior predictive summary error.
- Boolean mechanism checks.
- Acceptance decision with reasons.

## Workflow
1. Compute centered vector correlation between posterior mean and true parameter.
2. Compute average absolute summary error for posterior predictive summaries.
3. Verify required mechanism flags: simulator executed, summaries conditioned, posterior estimator fit, posterior samples generated, no likelihood evaluation, and no original repository use.
4. Accept only if metric, summary error, and mechanism checks pass.

## Validation
Run `python tests/test_validation.py` from this skill directory.

## Limitations
Correlation against synthetic ground truth is a reduced validation target; full paper validation would compare richer posterior distributions and biological traces.
