---
name: tsnpe_sbcc_diagnostics
description: Compute TSNPE support inclusion and simulation-based coverage calibration diagnostics after each truncated proposal training round.
---

# Tsnpe Sbcc Diagnostics

Use this skill after each TSNPE round to check whether posterior credible regions cover simulated ground-truth parameters and whether the truncation support is not excluding likely true posterior mass. It reports numeric coverage and support-inclusion values for recovery analysis.

Inputs: JSON with `true_log_probs`, `posterior_sample_log_probs`, and `threshold`. Outputs: empirical coverage curve, ground-truth support fraction, and mechanism checks. Validation: run `python tests/test_sbcc.py`.

