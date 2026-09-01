---
name: tsnpe_sir_fallback_sampler
description: Run deterministic sampling-importance-resampling diagnostics for narrow TSNPE proposals.
---

# Tsnpe Sir Fallback Sampler

Use this skill when rejection sampling from the truncated proposal is too inefficient and a fixed candidate budget is needed. It computes normalized importance weights from log prior minus log posterior proposal values, seeded systematic resampling indices, and effective sample size. Do not treat SIR as valid if all weights collapse or ESS is not recorded.

Inputs: JSON with `candidate_samples`, `log_prior`, `log_proposal`, `num_samples`, and optional `seed`. Outputs: JSON with selected samples, normalized weights, ESS, and mechanism checks. Validation: run `python tests/test_sir.py`.

