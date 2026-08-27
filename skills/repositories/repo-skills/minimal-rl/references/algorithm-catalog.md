# minimalRL Algorithm Catalog

## Purpose

Read this when choosing which minimalRL algorithm route to load. The table uses source script names as provenance labels only; use the bundled sub-skill references and scripts for runtime guidance.

| Algorithm | Evidence script label | Environment | Action type | Main surfaces | Owning sub-skill |
|---|---|---|---|---|---|
| REINFORCE | `REINFORCE.py` | CartPole-v1 | Discrete, 2 actions | `Policy.forward`, `put_data`, `train_net` | [on-policy-discrete](../sub-skills/on-policy-discrete/SKILL.md) |
| Vanilla actor-critic | `actor_critic.py` | CartPole-v1 | Discrete, 2 actions | `ActorCritic.pi`, `v`, `make_batch`, `train_net` | [on-policy-discrete](../sub-skills/on-policy-discrete/SKILL.md) |
| PPO | `ppo.py` | CartPole-v1 | Discrete, 2 actions | `PPO.pi`, `v`, `make_batch`, GAE, clipped ratio | [on-policy-discrete](../sub-skills/on-policy-discrete/SKILL.md) |
| PPO-LSTM | `ppo-lstm.py` | CartPole-v1 | Discrete, 2 actions | `PPO.pi(x, hidden)`, `v(x, hidden)`, recurrent rollout data | [on-policy-discrete](../sub-skills/on-policy-discrete/SKILL.md) |
| V-trace | `vtrace.py` | CartPole-v1 | Discrete, 2 actions | `Vtrace.vtrace`, clipped `rho`/`c`, policy/value losses | [off-policy-value](../sub-skills/off-policy-value/SKILL.md) with network links to [on-policy-discrete](../sub-skills/on-policy-discrete/SKILL.md) |
| DQN | `dqn.py` | CartPole-v1 | Discrete, 2 actions | `ReplayBuffer`, `Qnet`, `train`, hard target network | [off-policy-value](../sub-skills/off-policy-value/SKILL.md) |
| ACER | `acer.py` | CartPole-v1 | Discrete, 2 actions | Sequence `ReplayBuffer`, `ActorCritic.pi/q`, truncated importance sampling | [off-policy-value](../sub-skills/off-policy-value/SKILL.md) |
| A2C | `a2c.py` | CartPole-v1 | Discrete, 2 actions | `ParallelEnv`, `worker`, `compute_target`, synchronous vector rollout | [parallel-actor-critic](../sub-skills/parallel-actor-critic/SKILL.md) |
| A3C | `a3c.py` | CartPole-v1 | Discrete, 2 actions | `global_model.share_memory`, `train`, `test`, local/global gradient copy | [parallel-actor-critic](../sub-skills/parallel-actor-critic/SKILL.md) |
| DDPG | `ddpg.py` | Pendulum-v1 | Continuous, 1 action | `MuNet`, `QNet`, OU noise, `soft_update`, replay | [continuous-control](../sub-skills/continuous-control/SKILL.md) |
| PPO-Continuous | `ppo-continuous.py` | Pendulum-v1 | Continuous, 1 action | Gaussian `PPO.pi`, value head, rollout minibatches, clipped ratio | [continuous-control](../sub-skills/continuous-control/SKILL.md) |
| SAC | `sac.py` | Pendulum-v1 | Continuous, 1 action | `PolicyNet`, twin `QNet`, `calc_target`, entropy temperature update | [continuous-control](../sub-skills/continuous-control/SKILL.md) |

## Fast route signals

- **CartPole + policy gradient / actor-critic / PPO**: start with [on-policy-discrete](../sub-skills/on-policy-discrete/SKILL.md).
- **CartPole + replay / target network / off-policy correction**: start with [off-policy-value](../sub-skills/off-policy-value/SKILL.md).
- **Pendulum + continuous actions**: start with [continuous-control](../sub-skills/continuous-control/SKILL.md).
- **Multiple processes / workers / pipes / shared memory**: start with [parallel-actor-critic](../sub-skills/parallel-actor-critic/SKILL.md).

## Common hyperparameter patterns

- CartPole examples generally use `gamma=0.98`; DDPG uses `gamma=0.99`; continuous PPO uses `gamma=0.9`.
- Several actor-critic variants scale CartPole rewards by `1/100`; continuous PPO and SAC scale Pendulum rewards by `1/10`; DDPG scales Pendulum rewards by `1/100`.
- Replay-based scripts wait for warm-up before training: DQN `>2000` transitions, ACER `>500` sequences, DDPG `>2000` transitions, SAC `>1000` transitions.
- PPO-family scripts store old action probabilities or log probabilities during rollout and compare them against current policy outputs during training.
