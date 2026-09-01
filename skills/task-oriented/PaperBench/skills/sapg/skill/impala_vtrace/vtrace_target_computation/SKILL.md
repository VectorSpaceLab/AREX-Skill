---
name: vtrace_target_computation
description: Compute IMPALA V-trace targets, clipped ratios, and policy-gradient advantages from off-policy trajectories.
---

Use this skill when a recovery or implementation needs the core IMPALA V-trace equations. Inputs are rewards, discounts, values with bootstrap, target action probabilities, behavior action probabilities, and clipping thresholds. Outputs are ratios, clipped `rho` and `c`, V-trace targets, and advantages.

Workflow: validate trajectory lengths, compute importance ratios, clip them separately for target residuals and trace cutting, run the backward recursive target, and report diagnostics. Use this skill before actor-critic updates; do not let a training harness duplicate the formula without cross-checking it.

Validation: tests cover on-policy reduction to n-step Bellman returns and off-policy clipping. Limitations: the helper is deterministic and vector-free for auditability, not a high-throughput learner implementation.

