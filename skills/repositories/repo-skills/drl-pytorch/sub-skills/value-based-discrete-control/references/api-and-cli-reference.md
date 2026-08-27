# Value-Based API and CLI Reference

DRL-Pytorch is a collection of standalone algorithm directories, not an installable package. Import names such as `DQN`, `utils`, and `main` collide across directories. Always isolate one algorithm directory at a time on `sys.path` or run commands from that directory.

## Import-path caveats

- Do not mix two value-based directories in the same Python import context without purging colliding modules such as `DQN`, `utils`, `PriorDQN`, `Categorical_DQN`, `NoisyNetDQN`, `LPRB`, and `Q_learning`.
- The launchers write and load checkpoints relative to the current working directory's `model/` folder. Run them from the owning algorithm directory or adjust paths deliberately.
- PER Gymnasium 0.2x modules choose their device internally with `torch.cuda.is_available()` and have no `--dvc` flag. Use `CUDA_VISIBLE_DEVICES=""` before Python starts when a CPU-only PER run is required.
- Use the bundled diagnostic [smoke_value_based.py](../scripts/smoke_value_based.py) for import and tiny network checks without training.

## Tabular Q-learning API

Directory label: `1.Q-learning`

| Symbol | Contract |
|---|---|
| `QLearningAgent(s_dim, a_dim, lr=0.01, gamma=0.9, exp_noise=0.1)` | Creates a NumPy Q table with shape `(s_dim, a_dim)`. |
| `select_action(s, deterministic)` | Deterministic mode returns `argmax(Q[s])`; non-deterministic mode uses epsilon-greedy exploration with `exp_noise`. |
| `train(s, a, r, s_next, dw)` | Applies `Q[s,a] += lr * (r + (1-dw)*gamma*max_a Q[s_next,a] - Q[s,a])`. |
| `save()` | Writes `model/q_table.npy` relative to current working directory. |
| `restore(npy_file='model/q_table.npy')` | Loads the Q table from the selected `.npy` file. |
| `evaluate_policy(env, agent)` | Resets a Gymnasium-style env and evaluates deterministic actions until termination or truncation. |

Launcher facts: the tabular `main.py` has no argparse flags, uses `CliffWalking-v0`, wraps train/eval envs with `TimeLimit`, trains for `Max_train_steps = 20000`, writes TensorBoard scalars, and saves the Q table at the end.

## DQN / DDQN / Dueling DQN

Directory label: `2.1_Duel-Double-DQN`

### Classes and functions

| Symbol | Contract |
|---|---|
| `build_net(layer_shape, activation, output_activation)` | Builds a sequential MLP from adjacent layer sizes. |
| `Q_Net(state_dim, action_dim, hid_shape)` | MLP Q network returning shape `(batch, action_dim)`. |
| `Duel_Q_Net(state_dim, action_dim, hid_shape)` | Dueling head with `Q = V + (A - mean(A))`. |
| `DQN_agent(**kwargs)` | Reads fields such as `state_dim`, `action_dim`, `dvc`, `Duel`, `Double`, `net_width`, `lr`, `gamma`, `batch_size`, `exp_noise`; owns `q_net`, target net, Adam optimizer, and `ReplayBuffer`. |
| `DQN_agent.select_action(state, deterministic)` | Uses greedy action when deterministic; otherwise epsilon-greedy via `exp_noise`. |
| `DQN_agent.train()` | Samples replay buffer, computes Double-DQN target when `Double=True`, optimizes MSE, and Polyak-updates target with `tau=0.005`. |
| `DQN_agent.save(algo, EnvName, steps)` / `load(...)` | Uses `model/{algo}_{EnvName}_{steps}.pth`. |
| `ReplayBuffer(state_dim, dvc, max_size=int(1e6))` | Stores tensors for `s`, `a`, `r`, `s_next`, and boolean `dw`; samples random indices. |
| `evaluate_policy(env, agent, turns=3)` | Deterministic multi-episode average. |
| `str2bool(v)` | Argparse boolean converter. |

### CLI flags

| Flag | Default | Notes |
|---|---:|---|
| `--dvc` | `cuda` | Use `cpu` for CPU-only runs. |
| `--EnvIdex` | `0` | `0` CartPole-v1, `1` LunarLander-v2. |
| `--write` | `False` | Enables `runs/{algo}-{brief}_S{seed}_...` TensorBoard logs. |
| `--render` | `False` | In render mode, evaluates in an infinite loop; pair with `--Loadmodel True` for play. |
| `--Loadmodel` | `False` | Loads from `model/{algo}_{brief}_{ModelIdex}.pth`. |
| `--ModelIdex` | `100` | CartPole pretrained example uses `100`; LunarLander example uses `400`. |
| `--Max_train_steps` | `1e6` | Set to `0` for safe construction-only smoke. |
| `--save_interval` | `50000` | Saves with `int(total_steps/1000)`. |
| `--eval_interval` | `2000` | Evaluation frequency. |
| `--random_steps` | `3000` | Random action warm-up. |
| `--update_every` | `50` | Runs 50 train updates every 50 env steps. |
| `--gamma`, `--net_width`, `--lr`, `--batch_size` | `0.99`, `200`, `1e-4`, `256` | Core hyperparameters. |
| `--exp_noise`, `--noise_decay` | `0.2`, `0.99` | Epsilon-greedy exploration and decay. |
| `--Double`, `--Duel` | `True`, `True` | Algorithm selector: default `DuelDDQN`; disable independently for DQN variants. |

## Prioritized replay DQN/DDQN

Directory labels: `2.3 .../LightPriorDQN_gym0.2x`, `2.3 .../PriorDQN_gym0.2x`, and legacy `2.3 .../PriorDQN_gym0.1x`.

### Recommended LightPrior Gymnasium 0.2x

| Symbol | Contract |
|---|---|
| `DQN_Agent(opt)` | Builds an MLP Q net, target net, Adam optimizer, Double-DQN toggle, epsilon schedule fields, and action selector. |
| `DQN_Agent.select_action(state, deterministic)` | Deterministic returns action; exploratory mode returns `(action, q_a)` so priority can be estimated immediately. |
| `DQN_Agent.train(replay_buffer)` | Samples LightPrior buffer, applies Double-DQN target when `DDQN=True`, weights TD error by normalized IS weights, clips gradients, updates priorities in-place, Polyak-updates target. |
| `LightPriorReplayBuffer(opt)` | Stores only current states plus actions/rewards/termination/truncation/priorities; derives `s_next` as `state[ind+1]` and excludes invalid boundary indices. |
| `LightPriorReplayBuffer.add(state, action, reward, dw, tr, priority)` | Adds one transition-like record with a precomputed priority. |
| `LightPriorReplayBuffer.sample(batch_size)` | Samples by `torch.multinomial`; returns `s, a, r, s_next, dw, tr, ind, Normed_IS_weight`. |
| `LinearSchedule(schedule_timesteps, initial_p, final_p).value(t)` | Linear interpolation for epsilon, beta, and LightPrior learning rate. |

LightPrior CLI flags: `--EnvIdex`, `--write`, `--render`, `--Loadmodel`, `--ModelIdex`, `--seed`, `--Max_train_steps`, `--buffer_size`, `--save_interval`, `--eval_interval`, `--warmup`, `--update_every`, `--gamma`, `--net_width`, `--lr_init`, `--lr_end`, `--lr_decay_steps`, `--batch_size`, `--exp_noise_init`, `--exp_noise_end`, `--noise_decay_steps`, `--DDQN`, `--alpha`, `--beta_init`, `--beta_gain_steps`, `--replacement`.

Important defaults: `--write True`, `--Max_train_steps 300000`, `--buffer_size 200000`, `--ModelIdex 250`, `--DDQN True`, `--alpha 0.6`, `--beta_init 0.4`, `--replacement False`. The default write behavior can create `runs/`; pass `--write False` for smokes.

### Sum-tree Gymnasium 0.2x

| Symbol | Contract |
|---|---|
| `DQN_Agent(opt)` | Similar DQN/DDQN model, using `opt.lr` rather than LightPrior's learning-rate schedule. |
| `PrioritizedReplayBuffer(opt)` | Stores NumPy arrays plus a `SumTree`; `sample(batch_size)` returns tensors and normalized IS weights. |
| `PrioritizedReplayBuffer.add(state, action, reward, next_state, dw)` | Adds transition and initializes priority to `1.0` or current max priority. |
| `update_batch_priorities(batch_index, td_errors)` | Rewrites sum-tree priorities as `(abs(td_error)+0.01)**alpha`. |
| `SumTree(buffer_capacity)` | Maintains priority sums in a `2*capacity-1` array and supports segment-based prioritized sampling. |

Sum-tree CLI flags largely match LightPrior, except it uses `--lr` instead of `--lr_init/--lr_end/--lr_decay_steps`, default `--buffer_size 100000`, default `--Max_train_steps 400000`, and default `--ModelIdex 50000`.

### Legacy Gym 0.1x

The legacy PER variant uses `gym==0.19.0`, Python 3.9-era dependencies, and the old `env.step(a) -> next_state, reward, done, info` API. Treat it as a comparison reference unless the user explicitly asks to recreate that legacy stack.

## C51 categorical DQN

Directory label: `2.4_Categorical-DQN_C51`

| Symbol | Contract |
|---|---|
| `Categorical_Q_Net(state_dim, action_dim, hid_shape, atoms)` | Network outputs logits over `action_dim * n_atoms`, softmaxes per action, and computes expected Q values from `atoms`. |
| `Categorical_Q_Net.forward(state, action=None)` | Returns selected action and the selected action's categorical distribution. If `action` is `None`, chooses argmax expected Q. |
| `CDQN_agent(**kwargs)` | Reads C51 fields including `v_min`, `v_max`, `n_atoms`, `DQL`, and standard DQN hyperparameters; owns categorical network, target net, replay buffer, and projection buffers. |
| `CDQN_agent.select_action(state, deterministic)` | Epsilon-greedy unless deterministic; greedy action comes from the categorical network. |
| `CDQN_agent.train()` | Computes categorical Bellman projection, optionally with Double Q-learning (`DQL=True`), and optimizes cross-entropy. |
| `ReplayBuffer` | Same tensor replay structure as DQN family. |
| `render_policy(env, agent, opt)` | Rendering helper that also plots distributions; requires Matplotlib. |

CLI additions beyond DQN-family flags: `--DQL True`, `--v_min -100`, `--v_max 100`, `--n_atoms 51`. Checkpoints use a `k` suffix: `model/{algo}_{brief}_{ModelIdex}k.pth`.

## NoisyNet DQN

Directory label: `2.5_NoisyNet-DQN`

| Symbol | Contract |
|---|---|
| `NoisyLinear(in_features, out_features, sigma_init=0.5)` | Factorized noisy linear layer with train-time noise reset and eval-time deterministic mean weights. |
| `Noisy_Q_Net(state_dim, action_dim, hid_shape)` | MLP Q network whose final layer is `NoisyLinear(..., sigma_init=0.25)`. |
| `NoisyNetDQN_agent(**kwargs)` | Standard DQN target/replay structure with `Noisy_Q_Net`; exploration is parameter noise, not epsilon-greedy. |
| `NoisyNetDQN_agent.select_action(state)` | Greedy argmax over the noisy Q network. |
| `NoisyNetDQN_agent.train()` | Standard DQN target with MSE loss and Polyak target update. |
| `ReplayBuffer` | Same tensor replay structure as DQN family, sized by `opt.buffer_size = min(1e6, Max_train_steps)`. |

NoisyNet CLI flags include `--dvc`, `--EnvIdex`, `--write`, `--render`, `--Loadmodel`, `--ModelIdex`, `--seed`, `--Max_train_steps`, `--save_interval`, `--eval_interval`, `--random_steps`, `--update_every`, `--gamma`, `--net_width`, `--lr`, and `--batch_size`. There are no `--exp_noise` or `--Double` flags.
