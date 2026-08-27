# Policy-Control API and CLI Reference

DRL-Pytorch is a collection of standalone algorithm directories rather than an installable Python package. Each directory has its own `utils.py` names and short imports. When importing modules from a checkout, isolate `sys.path` per algorithm directory and clear cached `utils`, `PPO`, `DDPG`, `TD3`, `SACD`, and `SAC` module names between algorithms. The bundled [../scripts/smoke_policy_control.py](../scripts/smoke_policy_control.py) follows this pattern.

## Launcher and agent inventory

| Workflow | Launcher | Agent class | Utility/network classes | Action space |
|---|---|---|---|---|
| PPO-Discrete | `3.1 PPO-Discrete/main.py` | `PPO.PPO_discrete` | `utils.Actor`, `utils.Critic`, `utils.evaluate_policy`, `utils.str2bool` | discrete |
| PPO-Continuous | `3.2 PPO-Continuous/main.py` | `PPO.PPO_agent` | `utils.BetaActor`, `utils.GaussianActor_musigma`, `utils.GaussianActor_mu`, `utils.Critic`, `utils.Action_adapter`, `utils.Reward_adapter` | continuous Box |
| DDPG | `4.1 DDPG/main.py` | `DDPG.DDPG_agent` | `utils.Actor`, `utils.Q_Critic`, `DDPG.ReplayBuffer`, `utils.evaluate_policy` | continuous Box |
| TD3 | `4.2 TD3/main.py` | `TD3.TD3_agent` | `utils.Actor`, `utils.Double_Q_Critic`, `TD3.ReplayBuffer`, `utils.Reward_adapter` | continuous Box |
| SAC-Discrete | `5.1 SAC-Discrete/main.py` | `SACD.SACD_agent` | `utils.Policy_Net`, `utils.Double_Q_Net`, `utils.ReplayBuffer`, `utils.evaluate_policy` | discrete |
| SAC-Continuous | `5.2 SAC-Continuous/main.py` | `SAC.SAC_countinuous` | `utils.Actor`, `utils.Double_Q_Critic`, `SAC.ReplayBuffer`, `utils.Action_adapter`, `utils.Action_adapter_reverse`, `utils.Reward_adapter` | continuous Box |

`SAC_countinuous` is misspelled in the source API; use that exact class name when constructing the SAC-Continuous agent.

## Common CLI flags

All six launchers expose these flags unless noted:

| Flag | Purpose | Safe-setting guidance |
|---|---|---|
| `--dvc` | Torch device string. Defaults to `cuda` in every policy-control launcher. | Pass `--dvc cpu` unless a CUDA build and GPU are confirmed. |
| `--EnvIdex` | Environment selector. | Use `0` for safe CPU baselines: CartPole for discrete, Pendulum for continuous. |
| `--write` | Enable TensorBoard `SummaryWriter`. | Use `False` for smoke checks; `True` writes under `runs/`. |
| `--render` | Create/render human display mode. | Use `False` on headless hosts. `True` enters an indefinite play loop when `--Loadmodel True`. |
| `--Loadmodel` | Load checkpoint before training/play. | Requires matching files under `model/`; leave `False` for construction checks. |
| `--ModelIdex` | Checkpoint index passed into each class's `load()`. | See checkpoint table in [algorithm-workflows.md](algorithm-workflows.md). |
| `--seed` | Random seed. | Launchers increment environment seeds across episodes to avoid overfitting a single reset seed. |
| `--Max_train_steps` | Training-loop budget. | `0` is the safe construction check. Real learning generally needs far more steps. |
| `--save_interval` | Save interval in raw environment steps. | Continuous/off-policy save methods often receive `int(total_steps/1000)`. |
| `--eval_interval` | Evaluation/logging interval. | Lowering this changes logging frequency but not action-space compatibility. |

## Algorithm-specific CLI flags

| Workflow | Extra flags | Meaning |
|---|---|---|
| PPO-Discrete | `--T_horizon`, `--gamma`, `--lambd`, `--clip_rate`, `--K_epochs`, `--net_width`, `--lr`, `--l2_reg`, `--batch_size`, `--entropy_coef`, `--entropy_coef_decay`, `--adv_normalization` | On-policy trajectory length, GAE/PPO coefficients, network width, optimizer settings, entropy decay, optional advantage normalization. |
| PPO-Continuous | `--Distribution`, `--T_horizon`, `--gamma`, `--lambd`, `--clip_rate`, `--K_epochs`, `--net_width`, `--a_lr`, `--c_lr`, `--l2_reg`, `--a_optim_batch_size`, `--c_optim_batch_size`, `--entropy_coef`, `--entropy_coef_decay` | Continuous PPO actor distribution plus separate actor/critic optimizer controls. `--Distribution` is `Beta`, `GS_ms`, or `GS_m`; default is `Beta`. |
| DDPG | `--gamma`, `--net_width`, `--a_lr`, `--c_lr`, `--batch_size`, `--random_steps`, `--noise` | Deterministic actor-critic with Gaussian exploration noise and warmup random actions. |
| TD3 | `--update_every`, `--delay_freq`, `--gamma`, `--net_width`, `--a_lr`, `--c_lr`, `--batch_size`, `--explore_noise`, `--explore_noise_decay` | Twin-delayed DDPG variant with target policy smoothing, delayed actor updates, batched update cadence, and decaying exploration noise. |
| SAC-Discrete | `--random_steps`, `--update_every`, `--gamma`, `--hid_shape`, `--lr`, `--batch_size`, `--alpha`, `--adaptive_alpha` | Categorical soft actor-critic with replay warmup, periodic update bursts, and optional adaptive entropy coefficient. |
| SAC-Continuous | `--update_every`, `--gamma`, `--net_width`, `--a_lr`, `--c_lr`, `--batch_size`, `--alpha`, `--adaptive_alpha` | Tanh-squashed Gaussian soft actor-critic with action scaling and optional adaptive entropy coefficient. |

## Actor and critic behavior

### PPO-Discrete

- `PPO_discrete(**kwargs)` builds an `Actor` and `Critic` on `dvc`.
- `Actor.pi(state, softmax_dim)` returns softmax probabilities over discrete actions.
- `select_action(s, deterministic)` expects a one-dimensional NumPy state. Deterministic mode returns `(argmax_action, None)`; stochastic mode samples `Categorical(pi)` and returns `(action_int, selected_action_probability)`.
- `put_data(s, a, r, s_next, logprob_a, done, dw, idx)` writes into fixed NumPy trajectory holders.
- `train()` computes GAE-style advantages using `dw` for bootstrap masking and `done` for trajectory termination, then applies PPO clipped updates.

### PPO-Continuous

- `PPO_agent(**kwargs)` chooses the actor from `kwargs["Distribution"]`:
  - `Beta`: `BetaActor`, with alpha/beta heads and Beta samples in `[0, 1]`.
  - `GS_ms`: `GaussianActor_musigma`, with learned mean and sigma heads.
  - `GS_m`: `GaussianActor_mu`, with learned mean and a shared learned log standard deviation.
- `select_action(state, deterministic)` returns normalized actions in `[0, 1]` plus per-action log probabilities when stochastic.
- `Action_adapter(a, max_action)` maps normalized `[0, 1]` actions to environment actions in `[-max_action, max_action]` with `2 * (a - 0.5) * max_action`.
- The `Critic` estimates state value, not Q value.

### DDPG

- `DDPG_agent(**kwargs)` builds a deterministic `Actor`, a single `Q_Critic`, target copies, Adam optimizers, and a replay buffer of size `5e5`.
- `select_action(state, deterministic)` returns the actor output in environment action scale. Stochastic mode adds Normal noise with standard deviation `max_action * noise` and clips to action bounds.
- The actor uses `tanh` multiplied by `max_action`; no separate action adapter is used.
- `train()` samples a replay batch, updates the critic by MSE target Q loss, updates the actor by maximizing critic value, and Polyak-updates target networks with `tau = 0.005`.

### TD3

- `TD3_agent(**kwargs)` builds a deterministic actor, a twin `Double_Q_Critic`, target copies, a replay buffer of size `1e6`, target-policy noise (`0.2 * max_action`), noise clipping (`0.5 * max_action`), and delayed actor updates.
- `select_action(state, deterministic)` mirrors DDPG but uses `explore_noise`.
- `train()` uses target-policy smoothing, clipped double Q targets, critic loss for both Q heads, and actor updates only when `delay_counter > delay_freq`.
- `Double_Q_Critic.Q1(state, action)` exposes only the first Q head for actor loss.

### SAC-Discrete

- `SACD_agent(**kwargs)` builds `Policy_Net`, `Double_Q_Net`, a target critic, and a replay buffer of size `1e6`.
- `Policy_Net.forward(s)` returns action probabilities via softmax.
- `select_action(state, deterministic)` returns `argmax` when deterministic or samples `Categorical(probs)` otherwise.
- With `adaptive_alpha=True`, the agent tracks `H_mean`, learns `log_alpha`, and uses target entropy `0.6 * (-log(1/action_dim))`.
- The launcher clips LunarLander terminal-crash rewards with `if r <= -100: r = -10` when `EnvIdex == 1`.

### SAC-Continuous

- `SAC_countinuous(**kwargs)` builds a tanh-squashed Gaussian `Actor`, twin `Double_Q_Critic`, target critic, replay buffer of size `1e6`, and optional adaptive alpha.
- `Actor.forward(state, deterministic, with_logprob)` returns normalized actions in `[-1, 1]` and optionally the tanh-corrected log probability.
- `Action_adapter(a, max_action)` maps `[-1, 1]` policy actions to `[-max_action, max_action]`.
- `Action_adapter_reverse(act, max_action)` maps sampled environment actions back into `[-1, 1]` before storing them in replay during warmup.
- `Reward_adapter` rescales/clips several continuous environments before storing rewards.

## Reward and action adapters

| Workflow | Adapter | Exact behavior |
|---|---|---|
| PPO-Continuous | `Action_adapter(a, max_action)` | Converts policy output `[0, 1]` to environment action `[-max_action, max_action]`. |
| PPO-Continuous | `Reward_adapter(r, EnvIdex)` | If `EnvIdex` is `0` or `1` and `r <= -100`, set `r = -1`; if `EnvIdex == 3`, set `r = (r + 8) / 8`; otherwise unchanged. The code comments are inconsistent with the current environment map, so preserve the code behavior when debugging. |
| TD3 | `Reward_adapter(r, EnvIdex)` | `EnvIdex 0`: `(r + 8) / 8`; `EnvIdex 1`: clip `r <= -100` to `-10`; `EnvIdex 4 or 5`: clip `r <= -100` to `-1`. |
| SAC-Discrete | inline launcher reward edit | For `EnvIdex 1` (`LunarLander-v2`), clip `r <= -100` to `-10`. |
| SAC-Continuous | `Action_adapter(a, max_action)` | Converts normalized policy action `[-1, 1]` to environment scale. |
| SAC-Continuous | `Action_adapter_reverse(act, max_action)` | Converts environment-scale sampled action back to normalized `[-1, 1]` for replay storage. |
| SAC-Continuous | `Reward_adapter(r, EnvIdex)` | Same reward mapping as TD3. |
| DDPG | none | Actor outputs are already scaled to environment action bounds by `tanh * max_action`. |

## Storage layouts

| Workflow | Storage object | Shapes and device |
|---|---|---|
| PPO-Discrete | NumPy holders on the agent | `s_hoder (T_horizon, state_dim)`, `a_hoder (T_horizon, 1)` int64, `r_hoder`, `s_next_hoder`, `logprob_a_hoder`, `done_hoder`, `dw_hoder`. |
| PPO-Continuous | NumPy holders on the agent | `s_hoder`, `a_hoder (T_horizon, action_dim)`, `r_hoder`, `s_next_hoder`, `logprob_a_hoder (T_horizon, action_dim)`, `done_hoder`, `dw_hoder`. |
| DDPG | `DDPG.ReplayBuffer` | Torch tensors on `dvc`: `s`, `a`, `r`, `s_next`, `dw`; max size `5e5`; actions are float vectors. |
| TD3 | `TD3.ReplayBuffer` | Torch tensors on `dvc`: `s`, `a`, `r`, `s_next`, `dw`; max size `1e6`; actions are float vectors. |
| SAC-Discrete | `utils.ReplayBuffer` | Torch tensors on `dvc`: `s`, `a` long shape `(max_size, 1)`, `r`, `s_next`, `dw`; max size `1e6`. |
| SAC-Continuous | `SAC.ReplayBuffer` | Torch tensors on `dvc`: `s`, normalized action `a`, `r`, `s_next`, `dw`; max size `1e6`. |

`dw` means terminal death/win and is used to mask bootstrapping. `tr` from Gymnasium means truncation. Launchers usually define `done = (dw or tr)` for episode-loop control but store only `dw` in replay/trajectory bootstrap masks.

## Import/object smoke coverage

The bundled smoke script checks these facts without training:

- PPO-Discrete imports `PPO_discrete`, constructs a small CPU agent, and samples a categorical action.
- PPO-Continuous imports `PPO_agent`, constructs selected actor distribution(s), and checks normalized action/log-prob shapes plus action scaling.
- DDPG, TD3, SAC-Discrete, and SAC-Continuous construct tiny CPU agents and call deterministic action selection.
- The script does not create Gymnasium environments, optional Box2D/MuJoCo tasks, TensorBoard writers, checkpoints, or downloads.
