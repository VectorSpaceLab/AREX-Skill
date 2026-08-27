# Workflows

This sub-skill covers the repo's on-policy family from Char02, Char03, Char04, and Char07. The key distinction is whether the policy update uses only returns, adds a learned baseline, uses parallel environments, or applies PPO clipping.

## Source map

| Workflow | Source evidence | What it teaches | Bundled support |
| --- | --- | --- | --- |
| REINFORCE / plain policy gradient | `Char02 Policy Gradient/REINFORCE.py`, `PolicyGradient.py`, `naive-policy-gradient.py` | Monte Carlo policy gradient on CartPole; `saved_log_probs`, episodic returns, reward normalization, no critic | `scripts/playback_saved_policy.py` for saved policy evaluation |
| MountainCar policy-gradient playback and training | `Char02 Policy Gradient/pytorch_MountainCar-v0.py`, `Run_Model.py` | Discrete MountainCar policy gradient, saved policy playback, and the checkpoint naming used by the original scripts | `scripts/playback_saved_policy.py` |
| Baseline and actor-critic | `Char02 Policy Gradient/REINFORCE_with_Baseline.py`, `Char03 Actor-Critic/AC_CartPole-v0.py`, `AC_MountainCar-v0.py` | Advantage-style updates, policy/value separation, and the difference between a pure policy and a value head | `scripts/playback_saved_policy.py` for full-model pickles |
| A2C with multiprocessing | `Char04 A2C/A2C.py`, `multiprocessing_env.py` | Subprocess vector envs, fixed-length rollouts, entropy bonus, and the helper used to fan out multiple classic-control envs | `scripts/multiprocessing_env.py` |
| PPO | `Char07 PPO/PPO2.py`, `PPO_CartPole_v0.py`, `PPO_MountainCar-v0.py`, `PPO_pendulum.py` | Clipped surrogate objective, buffer cadence, repeated minibatch updates, and the discrete vs continuous-action PPO split | reference notes below |

## How the families differ

| Family | Code signal | Update shape | Typical user request |
| --- | --- | --- | --- |
| REINFORCE | `saved_log_probs`, `rewards`, `finish_episode()` | Backward Monte Carlo return, normalize returns, policy loss only | "Run REINFORCE on CartPole" |
| Baseline / actor-critic | `value_head`, `state_value`, `SavedAction`, `G - V` | Policy loss plus value loss, advantage reduces variance | "Compare baseline vs no-baseline" |
| A2C | `SubprocVecEnv`, `num_envs`, `num_steps`, entropy bonus | Parallel rollouts over several envs, synchronous update from short segments | "Use the A2C multiprocessing helper" |
| PPO | `clip_param`, `ratio`, `torch.clamp`, `BatchSampler`, `ppo_epoch` | Reuse a buffer for several minibatch epochs while clipping policy drift | "Inspect PPO clipping" |

## Detailed workflow notes

### REINFORCE and policy gradient

- `REINFORCE.py` and `PolicyGradient.py` are the cleanest CartPole examples.
- `naive-policy-gradient.py` is a batch-update variant that accumulates state, action, and reward pools before each optimizer step.
- The common pattern is:
  1. sample an action from `Categorical(probs)`,
  2. store the log-probability,
  3. compute discounted returns backward,
  4. normalize returns,
  5. apply `-log_prob * return`.
- There is no learned baseline in the plain REINFORCE path.

### Baseline and actor-critic

- `REINFORCE_with_Baseline.py` introduces a value estimate to reduce variance.
- `AC_CartPole-v0.py` and `AC_MountainCar-v0.py` make the baseline explicit with separate policy and value heads.
- The conceptual test is `advantage = G - V(s)`.
- `AC_MountainCar-v0.py` also adds reward shaping with the current position term.
- Treat the baseline script as a conceptual reference if you are explaining the update flow; its implementation is rough, so prefer the actor-critic scripts when you need a clearer example.

### A2C with multiprocessing

- `A2C.py` creates `num_envs = 8` and a `SubprocVecEnv` instance from the bundled helper.
- It rolls out `num_steps = 5` per update, then computes returns, advantages, and an entropy bonus.
- `test_env()` runs a single evaluation env for quick reward checks.
- This workflow is the one that most depends on the bundled multiprocessing helper.

### PPO clipping and update cadence

- `PPO2.py` is the most explicit source for the clip math and the buffer/update relationship.
- The discrete PPO variants (`PPO_CartPole_v0.py`, `PPO_MountainCar-v0.py`) store action probabilities for `Categorical` policies and update after collecting enough transitions for a PPO batch.
- The Pendulum variant (`PPO_pendulum.py`) uses `Normal(mu, sigma)`, clamps the sampled action to `[-2, 2]`, and computes log-probabilities from the continuous distribution.
- The update gate differs by script:
  - `PPO2.py`: `buffer_capacity = 1000`, `batch_size = 8`, `ppo_epoch = 10`.
  - `PPO_CartPole_v0.py`: updates when the episode ends and the buffer is large enough.
  - `PPO_MountainCar-v0.py`: `buffer_capacity = 8000`, `batch_size = 32`, `ppo_update_time = 10`.
  - `PPO_pendulum.py`: `buffer_capacity = 1000`, `batch_size = 32`, `ppo_epoch = 10`.
- The clipping term is `torch.clamp(ratio, 1 - clip_param, 1 + clip_param)` and is meant to keep the new policy close to the old one.
- `PPO2.py` also writes TensorBoard scalars under `../exp`.
- The source has some rough edges; use it to understand the objective and cadence, not as a literal production-ready implementation.

### Saved policy playback

- `Run_Model.py` is the original MountainCar playback recipe for `policyNet.pkl`.
- `AC_CartPole-v0.py` and `AC_MountainCar-v0.py` save full model pickles that the bundled playback helper can evaluate if the class names still match.
- `PPO_pendulum.py` saves `state_dict`s for actor and critic separately; those are not full-model pickles and need manual reconstruction.
- If you only need to verify that a saved policy can act in the environment, the bundled helper is the preferred path.

## Checkpoint and log conventions

| File / folder pattern | Meaning | Playback / inspection note |
| --- | --- | --- |
| `policyNet.pkl` | Saved MountainCar policy object from the playback recipe | Load with the bundled playback helper or an equivalent `torch.load` path |
| `AC_CartPole_Model/ModelTraing*.pkl` | Pickled CartPole actor-critic model objects | Full-model pickle; load only if the `Policy` class layout is available |
| `AC_MountainCar-v0_Model/ModelTraing*.pkl` | Pickled MountainCar actor-critic model objects | Full-model pickle; use the bundled playback helper or a matching class definition |
| `param/ppo_anet_params.pkl`, `param/ppo_cnet_params.pkl` | PPO Pendulum `state_dict`s | Recreate the actor and critic classes before loading |
| `../param/net_param/*.pkl` | PPO discrete model weights in the source family | Inspect as state_dict-style checkpoints, not as pickled modules |
| `../exp` | TensorBoard logs from PPO variants | Relative to the process working directory; inspect with TensorBoard if logs are missing |

## Environment and API notes

- The repo scripts assume old Gym-style `env.reset()` and 4-value `env.step(...)` signatures.
- `env.seed(...)` still appears throughout the source; on Gymnasium or newer Gym releases, switch to `reset(seed=...)` and update step unpacking.
- `CartPole-v0` and `MountainCar-v0` are supported in the inspected environment.
- `Pendulum-v0` is legacy; use `Pendulum-v1` in the inspected environment when you want the modern substitute.
- Keep this sub-skill CPU-first. CUDA is available in the inspection environment, but none of the on-policy workflows require a GPU to understand or route correctly.
