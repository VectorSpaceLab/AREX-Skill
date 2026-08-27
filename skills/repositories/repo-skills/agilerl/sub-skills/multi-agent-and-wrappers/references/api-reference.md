# Multi-Agent API Reference

## Algorithms

- `agilerl.algorithms.maddpg.MADDPG`
- `agilerl.algorithms.matd3.MATD3`
- `agilerl.algorithms.ippo.IPPO`

Prefer `create_population(algo="MADDPG" | "MATD3" | "IPPO", ...)` for normal workflows.

## Training Helpers

- `agilerl.training.train_multi_agent_off_policy.train_multi_agent_off_policy(...)`
- `agilerl.training.train_multi_agent_on_policy.train_multi_agent_on_policy(...)`

## Vector Environments

- `agilerl.vector.pz_async_vec_env.AsyncPettingZooVecEnv`
- `agilerl.vector.pz_vec_env.PettingZooVecEnv`
- `agilerl.utils.utils.make_multi_agent_vect_envs(...)`

## Buffers And Wrappers

- `agilerl.components.multi_agent_replay_buffer.MultiAgentReplayBuffer`
- `agilerl.wrappers.agent.AsyncAgentsWrapper`
- `agilerl.wrappers.pettingzoo_wrappers.PettingZooAutoResetParallelWrapper`
- `agilerl.wrappers.learning.Skill`

## Key Data Structures

Multi-agent transitions are usually dictionaries keyed by agent ID. Keep key sets and ordering consistent across observations, actions, rewards, terminations, truncations, and infos.
