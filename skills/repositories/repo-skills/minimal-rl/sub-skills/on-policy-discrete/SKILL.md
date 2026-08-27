---
name: on-policy-discrete
description: "Guides minimalRL single-process discrete CartPole policy-gradient,
  actor-critic, PPO, PPO-LSTM, and V-trace policy/value workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# On-Policy Discrete Workflows

Use this sub-skill when a task asks about minimalRL's single-process discrete-action CartPole algorithms: REINFORCE, vanilla actor-critic, discrete PPO, PPO-LSTM, or the policy/value side of V-trace.

## Route by task

- **REINFORCE or Monte-Carlo policy gradient**: read [references/api-reference.md](references/api-reference.md) for the `Policy` contract and [references/workflows.md](references/workflows.md) for the return/backprop loop.
- **Vanilla actor-critic**: use [references/workflows.md](references/workflows.md) for rollout batches and TD advantage, then [references/api-reference.md](references/api-reference.md) for `ActorCritic.pi`, `v`, `make_batch`, and `train_net`.
- **Discrete PPO / GAE**: use [references/workflows.md](references/workflows.md) for clipped surrogate and GAE decisions. Check [references/troubleshooting.md](references/troubleshooting.md) when ratios, `prob_a`, or advantage tensors misbehave.
- **Recurrent PPO**: use the PPO-LSTM sections in [references/api-reference.md](references/api-reference.md) and [references/troubleshooting.md](references/troubleshooting.md) for hidden-state shape and detach issues.
- **V-trace policy/value mechanics**: use this sub-skill for policy/value network shapes; route replay and off-policy correction depth to [../off-policy-value/SKILL.md](../off-policy-value/SKILL.md).

## Do not use this sub-skill for

- DQN, ACER replay buffers, target networks, or off-policy correction debugging; use [../off-policy-value/SKILL.md](../off-policy-value/SKILL.md).
- DDPG, SAC, or continuous PPO for Pendulum; use [../continuous-control/SKILL.md](../continuous-control/SKILL.md).
- A2C/A3C multiprocessing, worker processes, or Gym API modernization for parallel scripts; use [../parallel-actor-critic/SKILL.md](../parallel-actor-critic/SKILL.md).

## Quick operating workflow

1. Identify the algorithm and action space. All workflows here assume CartPole-style observations of length 4 and 2 discrete actions unless you are intentionally porting.
2. Read the relevant API contract in [references/api-reference.md](references/api-reference.md) before changing shapes, tuple fields, or update loops.
3. When porting to another discrete environment, update input dimension, output action count, `softmax_dim`, reward scaling, and termination handling together; see [references/workflows.md](references/workflows.md).
4. Run the bundled shape smoke helper before attempting long training:

   ```bash
   python sub-skills/on-policy-discrete/scripts/smoke_on_policy_discrete.py --algorithm all
   ```

5. If the failure involves Gym reset/step arity, PyTorch graph reuse, probability zeros, or hidden-state shapes, read [references/troubleshooting.md](references/troubleshooting.md) before editing the algorithm.

## Bundled runtime files

- [references/api-reference.md](references/api-reference.md) records source-faithful classes, methods, hyperparameters, tensor shapes, and data tuple contracts.
- [references/workflows.md](references/workflows.md) explains how to choose and adapt REINFORCE, actor-critic, PPO, PPO-LSTM, and V-trace policy/value logic.
- [references/troubleshooting.md](references/troubleshooting.md) maps common symptoms to concrete fixes.
- [scripts/smoke_on_policy_discrete.py](scripts/smoke_on_policy_discrete.py) is a safe CPU-only helper that validates representative model, data, and tensor-shape contracts without importing the original repository or running training.
