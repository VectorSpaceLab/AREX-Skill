---
name: actor_learner_protocol
description: Validate IMPALA actor learner unrolls with behavior and learner policy metadata for V-trace recovery.
---

Use this skill when constructing or checking IMPALA-style trajectories before V-trace computation. It should not compute losses or update parameters.

Inputs: rewards, discounts, actions, values including bootstrap, learner policy distributions, and behavior policy distributions.
Outputs: validated JSON with action probabilities and policy-lag diagnostics.

Workflow: load an unroll, check dimensions and probability distributions, extract probabilities for each action, and emit a compact validated record. Preserve both learner and behavior policy metadata because treating the sample as on-policy violates the paper mechanism.

Validation: run `python tests/test_protocol.py` or validate the skill tree with tests. Limitations: this skill uses small JSON fixtures and does not launch distributed actors.

