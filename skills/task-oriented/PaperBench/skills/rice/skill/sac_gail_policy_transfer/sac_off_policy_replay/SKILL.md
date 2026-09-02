---
name: sac_off_policy_replay
description: Build and sample validated off-policy replay batches for Soft Actor-Critic recovery harnesses.
---

# SAC Off-Policy Replay

Use this skill when a SAC experiment needs a compact replay-buffer abstraction that stores transitions and produces deterministic minibatches. Do not compute SAC losses here.

## Inputs
- Transition records containing `state`, `action`, `reward`, `next_state`, `done`, and `log_prob`.
- Optional integer sample indices.

## Outputs
- A validated replay batch.
- Summary counts and deterministic sampled transitions.

## Workflow
1. Validate every transition has the required fields.
2. Convert numeric fields to finite floats and `done` to bool.
3. Preserve the stored transition order.
4. Sample by explicit indices so tests and recovery runs are reproducible.

## Validation
Run `python tests/test_replay.py` or validate the full skill tree with the Distiller validator.

## Limitations
This is a bounded recovery utility, not a high-throughput production replay buffer.
