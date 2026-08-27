# Multi-Agent Workflows

## PettingZoo Vectorization

AgileRL builds multi-agent workflows around PettingZoo-style parallel environments.

```python
from pettingzoo.mpe import simple_speaker_listener_v4
from agilerl.utils.utils import make_multi_agent_vect_envs

def make_env():
    return simple_speaker_listener_v4.parallel_env(continuous_actions=True)

env = make_multi_agent_vect_envs(make_env, num_envs=8)
```

Use an environment factory, not a single already-created environment, so vectorization can create independent workers.

## Agent IDs And Spaces

AgileRL expects:

- `agent_ids`: unique IDs such as `speaker_0`, `listener_0`.
- `observation_spaces`: one observation space per agent ID in matching order.
- `action_spaces`: one action space per agent ID in matching order.

Homogeneous groups use the prefix before `_`, such as `speaker` or `listener`. This supports group-level architecture config and, for supported algorithms, parameter sharing.

## Off-Policy Multi-Agent

Use `MADDPG` or `MATD3` for off-policy multi-agent tasks. Add `MultiAgentReplayBuffer` and train with `train_multi_agent_off_policy(...)`.

## On-Policy Multi-Agent

Use `IPPO` for independent PPO-style workflows. Train with `train_multi_agent_on_policy(...)` and configure group-level policies when using homogeneous agents.

## Asynchronous Agents

Some PettingZoo environments only return observations for agents that should act next. `AsyncAgentsWrapper` processes observations/actions to be compatible with AgileRL vector envs for supported algorithms (`IPPO`, `MADDPG`, `MATD3`). Validate with tiny synthetic spaces before full training.

## Curriculum And Skill Wrappers

AgileRL wrapper utilities can express hierarchical skill/curriculum environments. Treat these as environment design concerns first: validate wrapped environment observation/action spaces, rewards, and resets before introducing population HPO.
