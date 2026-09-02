---
name: tsnpe_hpr_truncated_proposal
description: Compute TSNPE high-posterior-density truncation thresholds and rejection samples from a bounded prior.
---

# Tsnpe Hpr Truncated Proposal

Use this skill when implementing or checking the TSNPE proposal update: estimate the epsilon HPR threshold from posterior log probabilities at the observation, then accept only prior samples whose posterior log probability is above that threshold. Do not use it for APT/SNPE-C atomic-loss corrections.

Inputs: a JSON file with `posterior_log_probs`, `prior_samples`, `prior_log_probs_for_samples`, `epsilon`, and optional `min_acceptance_rate`. Outputs: JSON containing `threshold`, `accepted_indices`, `accepted_samples`, `acceptance_rate`, and `mechanism_checks`.

Workflow: validate finite numeric arrays; compute the epsilon quantile threshold; build the support mask; fail if no samples are accepted; record whether the proposal is prior-proportional inside support. Validation: run `python tests/test_hpr.py`.

