---
name: sbi_posterior_interface_and_diagnostics
description: Summarize posterior samples and validate SBI uncertainty with finite-sample and reference checks.
---

# SBI Posterior Interface And Diagnostics

Use this skill when an SBI workflow has produced posterior samples or a posterior-like object and needs sample summaries and mechanism-focused diagnostics.

Do not use it to train the posterior estimator.

## Inputs
- Posterior samples or sample-producing posterior object.
- Observation metadata.
- Optional reference posterior summary.
- Thresholds for mean error and uncertainty sanity checks.

## Outputs
- Sample mean, standard deviation, count, and finite status.
- Reference comparison metrics when available.
- Diagnostic pass/fail report and mechanism-check fields.

## Workflow
1. Normalize samples to a numeric list or two-dimensional array.
2. Check finite values and non-degenerate uncertainty.
3. Compute summary statistics.
4. Compare with reference values when supplied.
5. Return explicit pass/fail diagnostics without fabricating unavailable log probabilities.

## Validation
Run:

```bash
python scripts/diagnose_posterior.py --samples-json '[1.0, 1.1, 0.9]'
python tests/test_diagnose_posterior.py
```

## Limitations
- Reference likelihoods are for evaluation only; they must not be required by the SBI training loop.
- Some posterior implementations support sampling but not density evaluation.
