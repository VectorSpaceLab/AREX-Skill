# Algorithm Troubleshooting

Use this reference when adapting PARL algorithms or examples fails. Start with the smallest failing surface: backend import, algorithm export, model-method check, tensor shape, training-loop state, then environment/distributed concerns.

## Backend and import failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `parl.algorithms.<Name>` is missing | Backend selected at import time does not export that class, or the class exists only in a module. | Set `PARL_BACKEND` explicitly and run `scripts/inspect_algorithm_catalog.py --backend <backend>`. For `IQL`, verify whether module-level import is needed in the target package. |
| Torch/Paddle/Fluid import fails | Selected backend package or one of PARL's import dependencies is absent. | Do not install into a shared environment automatically. Use the catalog inspector's static fallback or prepare an isolated environment. |
| Code imports PARL before setting `PARL_BACKEND` | Backend auto-selection already happened. | Move backend selection before the first `import parl` or restart the Python process. |
| Fluid code breaks on modern Paddle/Python | Legacy backend/API mismatch. | Treat Fluid guidance as source-backed legacy material. Use Paddle or Torch unless the task requires Fluid. |

## Model-method errors

PARL algorithms call `check_model_method` for many required methods. If instantiation fails, compare the model against `algorithm-catalog.md`.

| Algorithm | Common missing method | Fix |
| --- | --- | --- |
| `PolicyGradient` | `forward` | Return action probabilities for the given observation batch. |
| `DQN` / `DDQN` | `forward` | Return Q-values for every action, not a sampled action. |
| `DDPG` / `SAC` / `OAC` / `CQL` | `policy`, `value`, actor/critic parameter group methods | Split actor and critic submodules and return parameters from each group. |
| `TD3` | `Q1` | Add a method that returns the first critic's Q-value for actor loss. |
| `A2C` | `policy_and_value` | Provide a combined call that returns policy logits/probabilities and value in one forward pass. |
| `QMIX` | `agent_model.init_hidden`, mixer `n_agents` | Use recurrent agent model state and mixer metadata. |
| `COMA` | actor recurrent hidden initializer | Ensure `model.actor_model.init_hidden()` exists and returns the expected hidden state. |
| `MAPPO` | `actor`, `critic`, `act_dim` | Match the MAPPO class's actor/critic submodule assumptions. |
| `DecisionTransformer` | `get_action` | Separate training `forward` from inference-time action selection. |
| `IQL` | `qvalue`, value parameter group | Provide Q-network and V-network separately. |

## Tensor and shape mismatches

- DQN action tensors must be integer indices with a gather-compatible shape, commonly `[batch_size, 1]`.
- `terminal` / `done` tensors should be numeric masks where `1` marks terminal and `0` marks continuing transitions, matching the algorithm's target calculation.
- Continuous actions must be scaled to the environment action bounds outside the algorithm when the model emits normalized actions.
- PPO/A2C rollouts must keep `obs`, `action`, `logprob`, `value`, `reward`, and `done` arrays aligned across time.
- Multi-agent tensors must preserve agent order; a shuffled agent dimension silently corrupts centralized critic inputs.
- Offline datasets must keep observation/action normalization consistent between dataset construction and training.

## Target-network and parameter-group mistakes

| Symptom | Check |
| --- | --- |
| Target network never changes | Call `sync_target()` at the intended interval, or pass the appropriate decay/tau when the algorithm supports soft update. |
| Actor and critic optimizers update the same parameters | `get_actor_params()` and `get_critic_params()` should return disjoint parameter sets unless the model intentionally shares a trunk. |
| TD3 actor loss fails | Confirm `Q1(obs, policy(obs))` returns a scalar/vector Q suitable for `mean()`. |
| SAC/CQL entropy behavior is unstable | Check action distribution log standard deviation clipping, `alpha`, and automatic entropy tuning settings. |

## Training-loop mistakes

- On-policy algorithms (`PPO`, `A2C`, `IMPALA`) should not reuse old replay samples as if they were off-policy transitions.
- Off-policy algorithms (`DQN`, `DDPG`, `TD3`, `SAC`, `OAC`, `CQL`) need replay or dataset batches with matching next-state and terminal fields.
- Offline algorithms (`CQL`, `IQL`, `DecisionTransformer`) should not depend on live environment exploration for their core learner check.
- A one-episode smoke run only proves wiring. It does not prove convergence, benchmark parity, or numerical stability.
- Rendering, video recording, and checkpoint writing should be disabled by default in reusable recipes.

## Environment and dependency issues

| Workflow | Common blocker | Safe response |
| --- | --- | --- |
| QuickStart / DQN CartPole | Gym API changed from 4-return to 5-return step format. | Use a compatibility wrapper and keep reset/step normalization in one place. |
| Atari A2C/PPO/DQN variants/IMPALA | `atari-py`, ROMs, OpenCV, and old Gym versions may conflict. | Use help/import checks first; isolate full Atari runs. |
| MuJoCo DDPG/TD3/SAC/OAC/PPO/CQL/ES | MuJoCo or D4RL dependency missing or version-specific. | Verify simulator import and dataset availability separately from algorithm instantiation. |
| Multi-agent QMIX/MADDPG | SMAC/PettingZoo environment mismatch or missing maps. | Validate environment metadata and batch shapes before training. |
| xparl distributed examples | Port/process conflicts or remote worker serialization errors. | Route to `xparl-distributed`; do not start/stop clusters without permission. |

## Debug sequence

1. Run the catalog inspector with the intended backend.
2. Confirm the class is exported or identify the module-level import path.
3. Instantiate a tiny dummy model that implements the required methods.
4. Pass one synthetic batch through `predict`/`sample` and `learn`/`update` only if the backend is installed.
5. Add environment wrappers and real replay/rollout storage.
6. Add optional distributed actors, MuJoCo/Atari/SMAC/D4RL, or challenge components only after local shape checks pass.

## What to report

When handing off a failure, include:

- Backend and algorithm class.
- Whether failure happened at import, constructor, `predict`/`sample`, `learn`/`update`, evaluation, or distributed launch.
- Required model methods present/missing.
- Batch shapes and dtypes.
- Environment family and optional dependencies.
- Whether the attempted run was smoke-only, full training, TIPC, or challenge workflow.
