# Atari Runtime and Wrappers

## Purpose

Use this reference to answer DRL-Pytorch Atari Noisy/Duel/DDQN questions without
reopening source files. It covers environment-index mapping, command recipes,
algorithm toggles, wrapper behavior, checkpoint names, and optional dependency
boundaries.

## Safety and dependency gates

The Atari DQN workflow is not a safe default smoke because it creates Atari
environments before training starts. Before running real commands, confirm:

- `torch`, `numpy`, and `gymnasium` are installed.
- Atari support and ROM licensing are available: Gymnasium Atari extras plus
  accepted ALE ROMs. This skill does not download ROMs or accept licenses.
- `opencv-python` (imported as `cv2`) is installed when the wrapper pipeline is
  imported or frame warping is used.
- Rendering with `--render True` requires a display or virtual display and runs
  an evaluation loop rather than a one-shot command.
- CUDA is optional. The Atari launcher defaults to `--device cuda`; pass
  `--device cpu` for CPU-only checks.

For a safe no-ROM diagnostic, run the bundled script from the generated skill
root:

```bash
python sub-skills/atari-and-asl-workflows/scripts/smoke_atari_asl.py --repo-root <repo-root>
```

Add optional import probes only when needed:

```bash
python sub-skills/atari-and-asl-workflows/scripts/smoke_atari_asl.py --repo-root <repo-root> --probe-atari-wrappers
python sub-skills/atari-and-asl-workflows/scripts/smoke_atari_asl.py --repo-root <repo-root> --probe-envpool
```

These diagnostics import modules and run dummy CPU CNN forwards. They do not
create ROM environments, start EnvPool workers, train, render, or download data.

## Environment naming

Both Atari workflows use the same `AtariNames` mapping, but they append different
suffixes:

| Workflow | Formula | Example for Pong | Example for Enduro |
|---|---|---|---|
| Atari Noisy/Duel/DDQN | `Name[EnvIdex] + "NoFrameskip-v4"` | `PongNoFrameskip-v4` | `EnduroNoFrameskip-v4` |
| ASL EnvPool | `Name[EnvIdex] + "-v5"` | `Pong-v5` | `Enduro-v5` |

Important indexes:

| EnvIdex | Name | Atari DQN env | ASL env |
|---:|---|---|---|
| 20 | Enduro | `EnduroNoFrameskip-v4` | `Enduro-v5` |
| 37 | Pong | `PongNoFrameskip-v4` | `Pong-v5` |

Full mapping:

```text
 1 Alien              2 Amidar             3 Assault            4 Asterix
 5 Asteroids          6 Atlantis           7 BankHeist          8 BattleZone
 9 BeamRider         10 Berzerk           11 Bowling           12 Boxing
13 Breakout          14 Centipede         15 ChopperCommand    16 CrazyClimber
17 Defender          18 DemonAttack       19 DoubleDunk        20 Enduro
21 FishingDerby      22 Freeway           23 Frostbite         24 Gopher
25 Gravitar          26 Hero              27 IceHockey         28 Jamesbond
29 Kangaroo          30 Krull             31 KungFuMaster      32 MontezumaRevenge
33 MsPacman          34 NameThisGame      35 Phoenix           36 Pitfall
37 Pong              38 PrivateEye        39 Qbert             40 Riverraid
41 RoadRunner        42 Robotank          43 Seaquest          44 Skiing
45 Solaris           46 SpaceInvaders     47 StarGunner        48 Surround
49 Tennis            50 TimePilot         51 Tutankham         52 UpNDown
53 Venture           54 VideoPinball      55 WizardOfWor       56 YarsRevenge
57 Zaxxon
```

Use only indexes `1..57`. A missing key means the command will fail before any
useful RL work begins.

## Atari Noisy/Duel/DDQN command facts

Run real Atari commands from the Atari workflow directory of a DRL-Pytorch
checkout. These commands are intended for a user-supplied checkout and are not
bundled helper scripts.

```bash
cd <repo-root>/2.2_Noisy-Duel-DDQN-Atari
```

Default behavior:

- Environment: `--EnvIdex 37`, which maps to `PongNoFrameskip-v4`.
- Algorithm: vanilla DQN because `--Double False --Duel False --Noisy False`.
- Device: `--device cuda` unless overridden.
- Training horizon: `--Max_train_steps 1000000`.
- Replay warmup: `--random_steps 10000`.
- Replay size: `--buffersize 10000`, intentionally light compared with Nature
  DQN to save memory.
- Evaluation interval: `--eval_interval 5000`; save interval:
  `--save_interval 100000`.
- TensorBoard is disabled by default: `--write False`.
- Rendering is disabled by default: `--render False`.

### Algorithm toggles

`algo_name` is built by concatenating enabled prefixes in this order:
`Double-`, `Duel-`, `Noisy-`, then `DQN`.

| Intent | Flags | `algo_name` |
|---|---|---|
| Vanilla DQN | `--Double False --Duel False --Noisy False` | `DQN` |
| Double DQN | `--Double True --Duel False --Noisy False` | `Double-DQN` |
| Dueling DQN | `--Double False --Duel True --Noisy False` | `Duel-DQN` |
| NoisyNet DQN | `--Double False --Duel False --Noisy True` | `Noisy-DQN` |
| Double Dueling DQN | `--Double True --Duel True --Noisy False` | `Double-Duel-DQN` |
| Double Dueling Noisy DQN | `--Double True --Duel True --Noisy True` | `Double-Duel-Noisy-DQN` |

`--Noisy True` disables epsilon-greedy inside `select_action`; the Q-network's
NoisyLinear layers provide exploration. With `--Noisy False`, evaluation uses a
small epsilon (`0.01`) and training uses a linear schedule from `--init_e` to
`--final_e` over `--anneal_frac` steps.

### Pong and Enduro recipes

CPU environment-construction check for Pong DQN. This still requires Atari ROMs
and `cv2`; use the bundled smoke script if those are not installed.

```bash
python main.py --device cpu --EnvIdex 37 --Double False --Duel False --Noisy False --write False --render False --Max_train_steps 0
```

Train Pong with Double-Duel-Noisy DQN on a CUDA device after optional gates are
satisfied:

```bash
python main.py --device cuda --EnvIdex 37 --Double True --Duel True --Noisy True --write True --render False
```

Train Enduro with Double DQN on CPU for debugging, not performance:

```bash
python main.py --device cpu --EnvIdex 20 --Double True --Duel False --Noisy False --write False --render False
```

Play pretrained Enduro using the README's flag combination. The expected
checkpoint filename is `Double-Duel-DQN_EnduroNoFrameskip-v4_900k.pth` under the
Atari workflow's `model/` directory.

```bash
python main.py --device cpu --render True --EnvIdex 20 --Double True --Duel True --Noisy False --Loadmodel True --ModelIdex 900
```

Play pretrained Pong using Double-Duel-Noisy DQN. The expected checkpoint
filename is `Double-Duel-Noisy-DQN_PongNoFrameskip-v4_700k.pth`.

```bash
python main.py --device cpu --render True --EnvIdex 37 --Double True --Duel True --Noisy True --Loadmodel True --ModelIdex 700
```

## Checkpoint conventions

The Atari agent saves and loads with:

```text
ExperimentName = algo_name + "_" + EnvName
save/load path = ./model/{ExperimentName}_{index}k.pth
```

Examples:

| Flags | EnvIdex | ModelIdex | Expected checkpoint basename |
|---|---:|---:|---|
| `--Double True --Duel True --Noisy False` | 20 | 900 | `Double-Duel-DQN_EnduroNoFrameskip-v4_900k.pth` |
| `--Double True --Duel True --Noisy True` | 37 | 700 | `Double-Duel-Noisy-DQN_PongNoFrameskip-v4_700k.pth` |

Common mismatch causes:

- The requested `--ModelIdex` is in thousands of training steps and must match
  the trailing `_700k`, `_900k`, etc.
- `--Double`, `--Duel`, and `--Noisy` must match the checkpoint's algorithm
  prefix exactly.
- The current working directory must be the Atari workflow directory or the
  relative `./model/` lookup will point somewhere else.
- The generated skill does not bundle `.pth` files; users must provide the
  checkpoint separately.

## Wrapper pipeline

The Atari DQN environment constructor asserts that the environment name contains
`NoFrameskip`, then applies the following Tianshou-style preprocessing chain:

1. `gym.make(env_name, render_mode=...)`.
2. Optional `NoopResetEnv(noop_max=30)` when `--noop_reset True`; action `0` is
   assumed to be `NOOP`.
3. `MaxAndSkipEnv(skip=4)`, which repeats actions and max-pools the last two
   frames.
4. Optional `EpisodicLifeEnv` for training; evaluation disables episodic-life
   termination.
5. `FireResetEnv` when the unwrapped action meanings include `FIRE`.
6. `WarpFrame`, which uses OpenCV to convert RGB frames to grayscale and resize
   to `84x84`.
7. Optional `ClipRewardEnv`, enabled for training and disabled for evaluation.
8. `FrameStack(frame_stack=4)`, returning a `torch.uint8` tensor of shape
   `(4, 84, 84)`.

The wrapper code accepts both legacy Gym step/reset signatures and Gymnasium's
newer `(obs, reward, terminated, truncated, info)` API. Observations remain
`uint8`; the Q-net divides by `255` internally.

## Model and replay facts

- `Duel_Q_Net` and `Q_Net` both use the Nature-DQN convolutional trunk:
  `Conv2d(4,32,8,stride=4)`, `Conv2d(32,64,4,stride=2)`,
  `Conv2d(64,64,3,stride=1)`, flatten to `64*7*7`.
- `Duel_Q_Net` computes `Q = V + (A - mean(A))`.
- `--fc_width` defaults to `200` for the Atari DQN workflow.
- The replay buffer stores CPU tensors with shapes based on `(4,84,84)` and
  moves sampled batches to `opt.dvc`.
- Training begins only after `buffer.size >= --random_steps`; reducing
  `--Max_train_steps` to `0` avoids the loop but still creates the Atari envs.
