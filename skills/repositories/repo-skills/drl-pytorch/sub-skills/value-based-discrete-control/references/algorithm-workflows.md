# Value-Based Algorithm Workflows

This reference is self-contained for DRL-Pytorch's non-Atari value-based algorithms. Use it to choose an algorithm, form safe commands, map `EnvIdex`, name checkpoints, and avoid optional-dependency traps.

## Scope and routing

Use these workflows for tabular CliffWalking, CartPole-v1, and LunarLander-v2 discrete-action experiments. Do not use this sub-skill for Atari NoFrameskip environments or EnvPool/Actor-Sharer-Learner; those are separate Atari workflows even when the algorithm name contains DQN.

## Algorithm selection

| Need | Algorithm directory label | Main implementation | When to choose |
|---|---|---|---|
| Small tabular baseline | `1.Q-learning` | `QLearningAgent` | CliffWalking-v0, Q-table update demonstrations, no PyTorch network needed. |
| Baseline/deep Q variants | `2.1_Duel-Double-DQN` | `DQN_agent` | CartPole/LunarLander DQN, DDQN, Dueling DQN, or Dueling DDQN. |
| Fast prioritized replay | `2.3 .../LightPriorDQN_gym0.2x` | `DQN_Agent` + `LightPriorReplayBuffer` | Recommended PER path; Gymnasium 0.29 API and torch multinomial priorities. |
| Sum-tree prioritized replay | `2.3 .../PriorDQN_gym0.2x` | `DQN_Agent` + `PrioritizedReplayBuffer` | Use only when the user asks for a sum-tree PER comparison. |
| Legacy PER comparison | `2.3 .../PriorDQN_gym0.1x` | legacy `DQN_Agent` | Reference-only unless the user intentionally creates a Python 3.9 + gym 0.19 stack. |
| Distributional DQN | `2.4_Categorical-DQN_C51` | `CDQN_agent` | C51/categorical value distribution with configurable atoms and Double Q toggle. |
| Parameter-noise exploration | `2.5_NoisyNet-DQN` | `NoisyNetDQN_agent` | Exploration through NoisyLinear layers instead of epsilon-greedy flags. |

## Environment indexes

For the deep value-based launchers, `--EnvIdex` maps as follows:

| `EnvIdex` | Gymnasium environment | Brief name in checkpoints/logs | Dependency status |
|---:|---|---|---|
| `0` | `CartPole-v1` | `CPV1` | CPU-safe with base Gymnasium. |
| `1` | `LunarLander-v2` | `LLdV2` | Requires optional Box2D support, commonly installed as `gymnasium[box2d]`. |

Tabular Q-learning is fixed to `CliffWalking-v0` and wraps it with `TimeLimit` in the training launcher.

## CPU-safe command recipes

Run commands from the selected algorithm directory in a user checkout. These recipes construct the environment and agent, then exit without entering training where `--Max_train_steps 0` is supported.

### DQN / DDQN / Dueling DQN

```bash
python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0
```

Variant switches:

```bash
# Dueling Double DQN, the default
python main.py --dvc cpu --EnvIdex 0 --Duel True --Double True --write False --render False --Max_train_steps 0

# Double DQN without dueling heads
python main.py --dvc cpu --EnvIdex 0 --Duel False --Double True --write False --render False --Max_train_steps 0

# Dueling DQN without Double Q-learning
python main.py --dvc cpu --EnvIdex 0 --Duel True --Double False --write False --render False --Max_train_steps 0

# Vanilla DQN
python main.py --dvc cpu --EnvIdex 0 --Duel False --Double False --write False --render False --Max_train_steps 0
```

### Prioritized replay DQN/DDQN

The modern PER launchers do not provide a `--dvc` flag. For a CPU-only smoke on a CUDA-visible machine, hide CUDA at the shell level:

```bash
CUDA_VISIBLE_DEVICES="" python main.py --EnvIdex 0 --write False --render False --Max_train_steps 0
```

Use this in `LightPriorDQN_gym0.2x` for the recommended fast PER implementation. Use the same command in `PriorDQN_gym0.2x` only when validating the sum-tree implementation. Toggle Double Q-learning with:

```bash
CUDA_VISIBLE_DEVICES="" python main.py --EnvIdex 0 --DDQN False --write False --render False --Max_train_steps 0
```

### C51 categorical DQN

```bash
python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0
```

Double Q-learning inside C51 is controlled by `--DQL`:

```bash
python main.py --dvc cpu --EnvIdex 0 --DQL False --write False --render False --Max_train_steps 0
```

Distribution support defaults are `--v_min -100 --v_max 100 --n_atoms 51`.

### NoisyNet DQN

```bash
python main.py --dvc cpu --EnvIdex 0 --write False --render False --Max_train_steps 0
```

NoisyNet has no epsilon flag; the last layer uses NoisyLinear parameter noise and `select_action` greedily evaluates the noisy Q network.

### Tabular Q-learning

The tabular launcher has no CLI parser and trains by default. For diagnostics, prefer the bundled no-training smoke:

```bash
python scripts/smoke_value_based.py --repo-root <DRL-Pytorch-checkout> --algorithm q-learning
```

When writing custom code, instantiate `QLearningAgent(s_dim, a_dim, lr, gamma, exp_noise)`, call `select_action(s, deterministic=...)`, and update with `train(s, a, r, s_next, dw)`. Its `save()` writes `model/q_table.npy` relative to the current working directory.

## Training and play recipes

Training is stochastic and can take many thousands of steps. Remove `--Max_train_steps 0` only when the user actually wants training.

| Workflow | Default training length | Typical train command | Play/load command shape |
|---|---:|---|---|
| DQN family | `1e6` | `python main.py --dvc cpu --EnvIdex 0 --write True` | `python main.py --dvc cpu --EnvIdex 0 --render True --Loadmodel True --ModelIdex 100` |
| LightPrior PER | `3e5` | `CUDA_VISIBLE_DEVICES="" python main.py --EnvIdex 0 --write True` | `CUDA_VISIBLE_DEVICES="" python main.py --EnvIdex 0 --write False --render True --Loadmodel True --ModelIdex 250` |
| Sum-tree PER | `4e5` | `CUDA_VISIBLE_DEVICES="" python main.py --EnvIdex 0 --write True` | `CUDA_VISIBLE_DEVICES="" python main.py --EnvIdex 0 --write False --render True --Loadmodel True --ModelIdex 50000` |
| C51 | `400e3` | `python main.py --dvc cpu --EnvIdex 0 --write True` | `python main.py --dvc cpu --EnvIdex 0 --render True --Loadmodel True --ModelIdex 60` |
| NoisyNet | `6e5` | `python main.py --dvc cpu --EnvIdex 0 --write True` | `python main.py --dvc cpu --EnvIdex 0 --render True --Loadmodel True --ModelIdex 100` |

For LunarLander, add `--EnvIdex 1` only after Box2D support is installed and tested.

## Checkpoint naming

All checkpoint paths are relative to the selected algorithm directory's `model/` folder. The launchers create `model/` when needed.

| Workflow | Save/load pattern | Examples |
|---|---|---|
| Tabular Q-learning | `model/q_table.npy` | Q table saved by `QLearningAgent.save()`. |
| DQN family | `model/{algo}_{brief_env}_{steps}.pth` | `DuelDDQN_CPV1_100.pth`, `DuelDDQN_LLdV2_400.pth`. `steps` is saved as thousands (`int(total_steps/1000)`). |
| LightPrior PER | `model/{algo}_{brief_env}_{steps}.pth` | `DDQN_CPV1_250.pth` for `--ModelIdex 250`; `steps` is saved as thousands. |
| Sum-tree PER | `model/{algo}_{brief_env}_{steps}.pth` | `DDQN_CPV1_50000.pth` for `--ModelIdex 50000`; this implementation saves raw step counts. |
| C51 | `model/{algo}_{brief_env}_{steps}k.pth` | `C51_DDQN_CPV1_60k.pth`, `C51_DDQN_LLdV2_320k.pth`. |
| NoisyNet | `model/{algo}_{brief_env}_{steps}k.pth` | `NoisyNetDQN_CPV1_100k.pth`, `NoisyNetDQN_LLdV2_550k.pth`. |

The `algo` token is constructed from flags: DQN family uses `Duel` prefix plus `DDQN` or `DQN`; PER uses `DDQN` or `DQN`; C51 uses `C51_DDQN` or `DQN`; NoisyNet uses `NoisyNetDQN`.

## TensorBoard

Set `--write True` to create a `runs/` directory for DQN, PER, C51, or NoisyNet launchers. Then run:

```bash
tensorboard --logdir runs
```

The tabular Q-learning launcher always enables TensorBoard in its source defaults. If a no-write diagnostic is needed, use the bundled smoke script instead of the tabular training launcher.

## Optional Box2D caveats

`LunarLander-v2` requires Box2D support. If `--EnvIdex 1` fails during `gym.make`, switch to `--EnvIdex 0` for a base CPU smoke or install the optional extra in the active environment. Do not treat a missing Box2D extra as a failure of CartPole, CliffWalking, or the algorithm implementation.
