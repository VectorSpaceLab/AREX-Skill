---
name: off-policy-value
description: "Guides minimalRL DQN, ACER, and V-trace replay, target-network,
  and off-policy correction workflows for discrete control."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Off-Policy Value Workflows

Use this sub-skill when a task asks about minimalRL's discrete value-learning, replay-buffer, target-network, ACER, or V-trace correction logic.

## Route by task

- **DQN / replay buffer / target network**: read [references/api-reference.md](references/api-reference.md) for `ReplayBuffer`, `Qnet`, and `train` contracts, then [references/workflows.md](references/workflows.md) for the safe update flow.
- **ACER**: read [references/workflows.md](references/workflows.md) for sequence replay and truncated importance sampling, then [references/troubleshooting.md](references/troubleshooting.md) for probability-ratio failures.
- **V-trace off-policy correction**: use the V-trace section in [references/api-reference.md](references/api-reference.md) and [references/workflows.md](references/workflows.md); route single-process policy/value architecture questions to [../on-policy-discrete/SKILL.md](../on-policy-discrete/SKILL.md).
- **Shape-only or pre-training checks**: run [scripts/smoke_off_policy_value.py](scripts/smoke_off_policy_value.py).

## Do not use this sub-skill for

- REINFORCE, actor-critic, PPO, or recurrent PPO route selection; use [../on-policy-discrete/SKILL.md](../on-policy-discrete/SKILL.md).
- DDPG, continuous PPO, or SAC; use [../continuous-control/SKILL.md](../continuous-control/SKILL.md).
- A2C/A3C multiprocessing and worker lifecycle; use [../parallel-actor-critic/SKILL.md](../parallel-actor-critic/SKILL.md).

## Quick operating workflow

1. Identify whether the user is debugging value targets, replay sampling, behavior-policy probabilities, or target-network synchronization.
2. Check tuple contracts in [references/api-reference.md](references/api-reference.md) before changing replay buffer contents.
3. Use [references/workflows.md](references/workflows.md) to preserve the update order: sample replay, compute detached targets, optimize current network, then update target/behavior state as appropriate.
4. Run the bundled smoke helper before long training:

   ```bash
   python sub-skills/off-policy-value/scripts/smoke_off_policy_value.py --algorithm all
   ```

5. For `ValueError: Sample larger than population`, NaN ratios, gather shape failures, or stale target behavior, read [references/troubleshooting.md](references/troubleshooting.md).

## Bundled runtime files

- [references/api-reference.md](references/api-reference.md) records replay tuple contracts, classes, functions, hyperparameters, and tensor shapes.
- [references/workflows.md](references/workflows.md) explains DQN, ACER, and V-trace update sequences and adaptation rules.
- [references/troubleshooting.md](references/troubleshooting.md) gives symptom-to-fix guidance for replay and correction failures.
- [scripts/smoke_off_policy_value.py](scripts/smoke_off_policy_value.py) validates replay sampling and off-policy tensor contracts without importing the original repository or running full training.
