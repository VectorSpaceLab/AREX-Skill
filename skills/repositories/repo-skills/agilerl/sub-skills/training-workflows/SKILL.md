---
name: training-workflows
description: "Use AgileRL classical single-agent training workflows for
  Gymnasium PPO, DQN, RainbowDQN, DDPG, TD3, replay/rollout buffers, and
  distributed training setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AgileRL Training Workflows

Use this sub-skill for AgileRL classical single-agent RL training with Gymnasium environments: PPO on-policy, DQN/RainbowDQN/DDPG/TD3 off-policy, recurrent variants, population setup, replay or rollout buffers, and safe pre-flight checks before long runs.

## Read First

- `references/workflows.md` for on-policy/off-policy training recipes and population flow.
- `references/api-reference.md` for important training helper and buffer APIs.
- `references/configuration.md` for `INIT_HP`, `net_config`, YAML, logging, and environment patterns.
- `references/distributed-training.md` for Accelerate/distributed constraints.
- `references/troubleshooting.md` for shape, dependency, vector-env, W&B, and runtime failures.
- `scripts/agilerl_classic_smoke.py --help` for a no-training import/config probe.

## Route Within AgileRL

| Need | Route |
| --- | --- |
| Evolution/tournament/mutation configuration | `../hpo-and-mutation/SKILL.md` |
| Custom `net_config`, `EvolvableNetwork`, CNN/LSTM/MultiInput setup | `../evolvable-modules/SKILL.md` |
| Multi-agent PettingZoo training | `../multi-agent-and-wrappers/SKILL.md` |
| Offline datasets or contextual bandits | `../offline-bandits-data/SKILL.md` |
| LLM fine-tuning | `../llm-fine-tuning/SKILL.md` |

## Standard Classical Training Flow

1. Install AgileRL and verify imports; use the root `scripts/check_agilerl_install.py` if unsure.
2. Create or wrap a Gymnasium environment; prefer `make_vect_envs(env_name, num_envs=...)` for vectorized classical training.
3. Define `INIT_HP` with algorithm-specific keys and `POP_SIZE`.
4. Define `net_config` with `encoder_config` and `head_config` unless the default network is sufficient.
5. Create a population with `create_population(algo=..., observation_space=..., action_space=..., net_config=..., INIT_HP=..., population_size=..., num_envs=..., device=...)`.
6. For off-policy algorithms, create `ReplayBuffer`; for on-policy PPO, use rollout collection/training helpers rather than replay memory.
7. Configure `TournamentSelection` and `Mutations` in the HPO sub-skill.
8. Call `train_on_policy(...)` or `train_off_policy(...)`, or implement a custom loop following `references/workflows.md`.

## Algorithm Selection

- Use `PPO` for on-policy, stable policy-gradient workflows and recurrent PPO variants.
- Use `DQN` or `RainbowDQN` for discrete-action off-policy value learning.
- Use `DDPG` or `TD3` for continuous-action off-policy actor-critic workflows.
- Use `train_on_policy` for PPO and `train_off_policy` for DQN/RainbowDQN/DDPG/TD3 families.

## Safe Validation

Run a smoke check before training:

```bash
python scripts/agilerl_classic_smoke.py --algorithm DQN --env CartPole-v1
python scripts/agilerl_classic_smoke.py --algorithm PPO --env CartPole-v1
```

The helper checks imports, Gymnasium spaces, basic config shape, and algorithm family routing. It does not train or download anything.
