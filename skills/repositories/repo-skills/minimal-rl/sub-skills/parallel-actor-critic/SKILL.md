---
name: parallel-actor-critic
description: "Guides minimalRL A2C and A3C multiprocessing actor-critic
  workflows, Gym API migration, and safe process debugging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Parallel Actor-Critic Workflows

Use this sub-skill when a task asks about minimalRL's A2C or A3C scripts, especially synchronous vector rollouts, asynchronous workers, shared models, process lifecycle, or Gym API modernization.

## Route by task

- **A2C / synchronous vector rollout**: read [references/api-reference.md](references/api-reference.md) for `ParallelEnv`, `worker`, and `compute_target`; read [references/workflows.md](references/workflows.md) for the update sequence.
- **A3C / asynchronous global-local training**: use [references/workflows.md](references/workflows.md) for shared model and local gradient flow, then [references/troubleshooting.md](references/troubleshooting.md) for worker hangs or missing gradients.
- **Gym 0.26 migration**: read the migration section in [references/workflows.md](references/workflows.md) before running either full native script.
- **Safe preflight checks**: run [scripts/smoke_parallel_actor_critic.py](scripts/smoke_parallel_actor_critic.py), which avoids full training and unbounded process spawning.

## Do not use this sub-skill for

- Single-process REINFORCE, actor-critic, PPO, PPO-LSTM, or V-trace network/update basics; use [../on-policy-discrete/SKILL.md](../on-policy-discrete/SKILL.md).
- DQN, ACER, or replay/off-policy correction; use [../off-policy-value/SKILL.md](../off-policy-value/SKILL.md).
- DDPG, continuous PPO, or SAC; use [../continuous-control/SKILL.md](../continuous-control/SKILL.md).

## Quick operating workflow

1. Decide whether the user wants A2C's synchronous vectorized rollout or A3C's asynchronous worker updates.
2. Check [references/api-reference.md](references/api-reference.md) for exact actor-critic, worker, and target-return contracts.
3. If using modern Gym, apply the reset/step/seed migration in [references/workflows.md](references/workflows.md) before running full training.
4. Run a bounded smoke check:

   ```bash
   python sub-skills/parallel-actor-critic/scripts/smoke_parallel_actor_critic.py --check all
   ```

5. For deadlocks, tuple arity failures, gradient-copy bugs, or CPU oversubscription, read [references/troubleshooting.md](references/troubleshooting.md).

## Bundled runtime files

- [references/api-reference.md](references/api-reference.md) records A2C/A3C classes, functions, hyperparameters, worker protocol, and tensor shapes.
- [references/workflows.md](references/workflows.md) explains synchronous and asynchronous actor-critic workflows plus Gym migration.
- [references/troubleshooting.md](references/troubleshooting.md) gives conservative process-debugging guidance.
- [scripts/smoke_parallel_actor_critic.py](scripts/smoke_parallel_actor_critic.py) validates model, target-return, and bounded protocol contracts without full training.
