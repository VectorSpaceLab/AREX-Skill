---
name: vtrace_actor_critic_update
description: Run a deterministic V-trace actor-critic optimizer step with value loss and policy-gradient diagnostics.
---

Use this skill to test whether a learner update follows the IMPALA V-trace actor-critic mechanism. Inputs are a small unroll with features, rewards, actions, behavior probabilities, and scalar trainable parameters. Outputs include loss before/after, gradients, parameter changes, V-trace targets, and optimizer-state evidence.

Workflow: compute learner target probabilities, call the V-trace target helper, form value and policy losses, estimate gradients deterministically, apply a bounded optimizer step, and verify that parameters or optimizer state changed. This is appropriate for reduced recovery, not for claiming full Atari or DMLab reproduction.

Validation: the included test asserts a loss decrease and changed parameters on a lagged trajectory. Limitations: finite differences and scalar parameters are used only to keep recovery auditable and bounded.

