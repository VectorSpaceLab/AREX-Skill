# Dataset and d3rlpy-derived API reference

Use this reference when the task involves custom offline datasets, `MDPDataset`, d3rlpy-style algorithm construction, or the `d3rlpy_new` fork used by E2O.

## MDPDataset array contract

An `MDPDataset` represents a fixed batch of transitions and automatically splits them into episodes. The core arrays are:

| Array | Required | Expected shape | Meaning |
| --- | --- | --- | --- |
| `observations` | yes | `(N, obs_dim...)` | Observation at each step. Vector observations are usually `(N, dim_observation)`; image observations are usually `(N, C, H, W)`. |
| `actions` | yes | continuous `(N, act_dim)` or discrete `(N,)` | Action for each transition. |
| `rewards` | yes | `(N,)` or `(N, 1)` | Scalar reward for each transition. |
| `terminals` | yes | `(N,)` or `(N, 1)` | Environment terminal flags. Values should be binary or boolean-like. |
| `episode_terminals` | optional | first dimension `N` | Episode boundary flags. Useful when an episode ends by timeout rather than environment termination. |
| `timeouts` | optional in raw D4RL-style input | first dimension `N` | Timeout flags. When converting D4RL data, `episode_terminals = terminals OR timeouts` is the usual behavior. |

Before constructing or training on a custom dataset, run the bundled validator against a local `.npz` file. It checks required arrays, first-dimension length agreement, basic dimensionality, finite numeric values, and optional timeout/episode-terminal lengths.

Example validator usage:

```bash
python skills/disco/ai-optimizer/sub-skills/offline-rl/scripts/validate_mdp_dataset_npz.py custom_dataset.npz
```

If the target agent does not have this exact skill path available, run the script from its bundled location in the loaded skill.

## D4RL-style conversion notes

The d3rlpy-derived dataset loader follows these patterns:

- D4RL env names such as Hopper, HalfCheetah, Walker2d, Ant, Pen, Door, and Maze families are routed to a D4RL loader.
- The D4RL loader obtains arrays from `env.get_dataset()`.
- It constructs `episode_terminals` as logical OR of `terminals` and `timeouts`.
- It casts observations, actions, rewards, terminals, and episode terminals to `float32` before building `MDPDataset`.
- Some flows optionally normalize state or alter rewards, but those transforms should be explicit in a task record.

For custom data conversion, preserve a clear distinction between:

- environment terminal: actual task termination;
- timeout or administrative truncation: episode boundary but not necessarily terminal dynamics;
- dummy final observations/actions: sometimes used when converting D4RL-style sequences with terminal rewards.

## d3rlpy-derived package inventory

The E2O fork exports these public algorithm names from its d3rlpy-style package:

- Continuous algorithms: `AWAC`, `BC`, `BCQ`, `BEAR`, `COMBO`, `CQL`, `CRR`, `DDPG`, `E2O`, `IQL`, `MOPO`, `PLASWithPerturbation`, `SAC`, `TD3`, `TD3PlusBC`, `RandomPolicy`.
- Discrete algorithms: `DiscreteBC`, `DiscreteBCQ`, `DiscreteCQL`, `DQN`, `DoubleDQN`, `DiscreteSAC`, `DiscreteRandomPolicy`.
- Utilities: `get_algo(name, discrete)` and `create_algo(name, discrete, **params)` map snake-case names to algorithm classes.

The continuous registry accepts names such as `awac`, `bc`, `bcq`, `bear`, `combo`, `cql`, `crr`, `ddpg`, `e2o`, `iql`, `mopo`, `plas`, `sac`, `td3`, `td3_plus_bc`, and `random`. The discrete registry accepts `bc`, `bcq`, `cql`, `dqn`, `double_dqn`, `sac`, and `random`.

## Constructor signature highlights

The signatures are d3rlpy-style keyword-only constructors. Most classes share `batch_size`, `n_frames`, `n_steps`, `gamma`, `use_gpu`, `scaler`, `action_scaler`, `reward_scaler`, and `impl` controls. Important algorithm-specific knobs are below.

| Class | Key constructor controls |
| --- | --- |
| `AWAC` | `actor_learning_rate`, `critic_learning_rate`, `batch_size=1024`, `tau`, `lam`, `n_action_samples`, `n_critics`, `update_actor_interval`, `use_gpu`. |
| `BCQ` | actor/critic/imitator learning rates and encoders, `lam`, `n_action_samples=100`, `action_flexibility=0.05`, `rl_start_step`, `beta`, `n_critics`, `use_gpu`. |
| `DiscreteBCQ` | `learning_rate`, `batch_size=32`, `action_flexibility=0.3`, `beta`, `target_update_interval`, `use_gpu`. |
| `BEAR` | actor/critic/imitator/temp/alpha learning rates, `initial_temperature`, `initial_alpha`, `alpha_threshold`, `lam`, `n_action_samples`, `n_target_samples`, `n_mmd_action_samples`, `mmd_kernel`, `mmd_sigma`, `vae_kl_weight`, `warmup_steps`, `use_gpu`. |
| `CQL` | actor/critic/temp/alpha learning rates, `initial_temperature`, `initial_alpha`, `alpha_threshold=10.0`, `conservative_weight=5.0`, `n_action_samples`, `soft_q_backup`, `use_gpu`. |
| `DiscreteCQL` | `learning_rate`, `alpha`, `target_update_interval`, `n_critics`, `use_gpu`. |
| `COMBO` | CQL-like policy controls plus `dynamics`, `rollout_interval`, `rollout_horizon`, `rollout_batch_size`, `real_ratio`, `generated_maxlen`, `conservative_weight`, `soft_q_backup`, `use_gpu`. |
| `MOPO` | SAC-like controls plus `dynamics`, `rollout_interval`, `rollout_horizon`, `rollout_batch_size`, `lam`, `real_ratio`, `generated_maxlen`, `use_gpu`. |
| `E2O` | SAC-like actor/critic/temp controls, `n_critics`, `initial_temperature`, `use_gpu`; loaded from offline CQL-style artifacts in the provided online script. |
| `IQL` | actor/critic/value learning rates and encoders, `expectile=0.7`, `weight_temp=3.0`, `max_weight=100.0`, `n_critics`, `use_gpu`. |
| `TD3PlusBC` | TD3 actor/critic controls plus `alpha=2.5` and default `scaler='standard'`. Useful when comparing offline baselines. |

## UWAC class highlights

The UWAC implementation follows a BEAR/SAC template and adds uncertainty/dropout-related options in addition to BEAR-style MMD controls:

- Standard BEAR/SAC-like controls: actor/critic/imitator/temp/alpha learning rates, encoders, `batch_size`, `gamma`, `tau`, `n_critics`, `initial_temperature`, `initial_alpha`, `alpha_threshold`, `lam`, action sample counts, `mmd_kernel`, `mmd_sigma`, `vae_kl_weight`, `warmup_steps`, `use_gpu`.
- Additional uncertainty controls: `beta`, `clip_bottom`, `clip_top`, `use_exp_weight`, `var_Pi`, `q_penalty`, `use_exp_penalty`, and `dropout`.

Because not every checkout exposes a UWAC train script, prefer direct class instantiation or a deliberately adapted trainer when the script file is missing.

## Minimal custom-dataset flow

Use this conceptual flow after `.npz` validation succeeds:

```python
import numpy as np
from d3rlpy.dataset import MDPDataset

arrays = np.load("custom_dataset.npz", allow_pickle=False)

dataset = MDPDataset(
    observations=np.asarray(arrays["observations"], dtype=np.float32),
    actions=np.asarray(arrays["actions"], dtype=np.float32),
    rewards=np.asarray(arrays["rewards"], dtype=np.float32).reshape(-1),
    terminals=np.asarray(arrays["terminals"], dtype=np.float32).reshape(-1),
    episode_terminals=np.asarray(arrays["episode_terminals"], dtype=np.float32).reshape(-1)
    if "episode_terminals" in arrays
    else None,
)
```

If only `timeouts` exists, create episode terminals from `terminals OR timeouts` before building the dataset. If both `episode_terminals` and `timeouts` exist, document which one controls episode boundaries and why.
