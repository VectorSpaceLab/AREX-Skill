---
name: multi-agent-and-wrappers
description: "Use AgileRL multi-agent PettingZoo workflows, MADDPG/MATD3/IPPO,
  vector envs, wrappers, agent grouping, and multi-agent replay setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AgileRL Multi-Agent And Wrappers

Use this sub-skill for AgileRL multi-agent reinforcement learning with PettingZoo parallel environments, `MADDPG`, `MATD3`, `IPPO`, `AsyncPettingZooVecEnv`, `make_multi_agent_vect_envs`, multi-agent replay buffers, agent grouping, asynchronous-agent wrappers, and curriculum/Skill wrappers.

## Read First

- `references/workflows.md` for PettingZoo vectorization and multi-agent training flow.
- `references/api-reference.md` for major algorithms, vector envs, wrappers, and buffers.
- `references/configuration.md` for agent IDs, homogeneous groups, and nested `net_config`.
- `references/troubleshooting.md` for ordering, wrapper, and vector-env issues.
- `scripts/inspect_multi_agent_setup.py --help` for a no-training config probe.

## Boundaries

- Use `../hpo-and-mutation/SKILL.md` for tournament/mutation probabilities.
- Use `../evolvable-modules/SKILL.md` for network architecture details.
- Use `../training-workflows/SKILL.md` for single-agent Gymnasium workflows.
- This sub-skill owns PettingZoo and multi-agent-specific spaces, IDs, vectorization, wrappers, and replay layout.

## Multi-Agent Flow

1. Create a PettingZoo parallel environment factory.
2. Vectorize with `make_multi_agent_vect_envs(...)` or `AsyncPettingZooVecEnv`.
3. Capture `agent_ids`, `observation_spaces`, and `action_spaces` in the same order.
4. Define `net_config` globally, per agent, or per homogeneous group.
5. Create a population with `create_population(algo="MADDPG" | "MATD3" | "IPPO", ...)`.
6. Use `MultiAgentReplayBuffer` for off-policy multi-agent algorithms.
7. Configure HPO and call the matching multi-agent training helper.

## Supported Patterns

- `MADDPG` and `MATD3`: multi-agent off-policy actor-critic workflows.
- `IPPO`: independent PPO-style on-policy workflow, including homogeneous group parameter-sharing patterns.
- `AsyncAgentsWrapper`: asynchronous-turn handling for supported algorithms.
- `Skill`/curriculum wrappers: hierarchical curriculum-style workflows when the environment exposes lower-level skills.

## Safe Validation

```bash
python scripts/inspect_multi_agent_setup.py --agents speaker_0 listener_0
```

The helper validates ID prefixes, synthetic spaces, and grouped config shape. It does not import external PettingZoo environments or train.
