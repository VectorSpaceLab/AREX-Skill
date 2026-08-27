# Actor-Sharer-Learner Framework

## Purpose

Use this reference for DRL-Pytorch Actor-Sharer-Learner (ASL) questions:
EnvPool Atari training, process topology, shared replay placement, major flags,
time-feedback behavior, and safe boundaries. ASL is an optional, long-running,
multiprocessing workflow rather than a quick default smoke.

## Runtime gates

ASL requires more than the base CPU inspection dependencies:

- `envpool >= 0.6.6` on a supported platform; the repository describes Ubuntu
  18.04.1+ as the intended host family.
- PyTorch, NumPy, and TensorBoard.
- Atari environment support compatible with EnvPool.
- Optional CUDA devices when using the default device flags.
- Multiprocessing support from a real Python script entry point; avoid launching
  ASL from notebooks or interactive snippets.

The bundled diagnostic can import ASL utility modules and optionally test that
`envpool` imports, but it does not create EnvPool environments or start worker
processes:

```bash
python sub-skills/atari-and-asl-workflows/scripts/smoke_atari_asl.py --repo-root <repo-root> --probe-envpool
```

## Environment naming and default

ASL uses the Atari name table with the suffix `-v5`:

```text
ExpEnvName = Name[EnvIdex] + "-v5"
```

Defaults:

| Flag | Default | Meaning |
|---|---:|---|
| `--EnvIdex` | `1` | `Alien-v5` by default |
| `--seed` | `0` | RNG seed |
| `--max_train_steps` | `50000000` | total actor environment steps |
| `--eval_freq` | `5000` | learner backprop-step interval for evaluation upload |
| `--eval_envs` | `1` | vectorized evaluator env count |
| `--train_envs` | `128` | vectorized actor env count |
| `--batch_size` | `32` | learner batch size |
| `--TPS` | `8` | transitions per learner step target; DQN Nature equivalent is `32/4=8` |
| `--time_feedback` | `True` | enables actor/learner wait-time balancing |
| `--explore_steps` | `150000` | random actor steps before training |
| `--buffersize` | `1000000` | replay storage; must be at least `explore_steps` |
| `--DDQN` | `True` | `True` for DDQN target; `False` for DQN target |
| `--gamma` | `0.99` | discount factor |
| `--fc_width` | `512` | hidden width after convolution trunk |
| `--lr` | `6.25e-5` | Adam learning rate |
| `--hard_update_freq` | `2000` | target network update interval in backprop steps |
| `--upload_freq` | `50` | learner upload interval for actor model refresh |

Device defaults are CUDA-oriented:

| Flag | Default | Role |
|---|---|---|
| `--A_dvc` | `cuda:0` | Actor network inference device |
| `--B_dvc` | `cpu` | replay buffer storage device |
| `--L_dvc` | `cuda:0` | Learner training device |
| `--E_dvc` | `cuda:0` | Evaluator network device |

For CPU-only experiments, override all process devices explicitly:

```bash
python main.py --A_dvc cpu --B_dvc cpu --L_dvc cpu --E_dvc cpu
```

This still creates EnvPool Atari environments and multiple processes; it is not
as safe as the bundled import smoke.

## Process topology

ASL launches a `BaseManager`-managed `shared_data` object and then starts these
processes:

| Process | Count in launcher | Main responsibility | Key interactions |
|---|---:|---|---|
| Actor | `1` | Collect vectorized Atari transitions with EnvPool and epsilon-greedy policy | Adds `(s, a, r, done, consistent)` batches to Sharer; downloads latest model when Learner toggles `should_download` |
| Learner | `1` | Sample replay batches and optimize Q-net | Reads batches from Sharer; uploads actor model parameters; queues evaluator models |
| Evaluator | `3` | Evaluate queued learner models | Reads model snapshots; creates EnvPool evaluation envs; appends curve points |
| Recorder | `1` | Sort and write TensorBoard curves | Polls curve points and writes `ep_r` scalars |
| Sharer | managed object | Shared replay buffer, model state, counters, timing, curve queues | Coordinates process communication with simple busy-flag locks and deques |

The main launcher uses `mp.set_start_method('spawn')`, starts all processes,
joins every process except Recorder, then waits before terminating Recorder.
Long waits at shutdown are expected because Recorder sleeps and the main process
has a post-join delay.

## Actor role

The Actor builds:

```text
envpool.make_gym(ExpEnvName, num_envs=train_envs, seed=seed,
                 max_episode_steps=int(50000 / 4),
                 episodic_life=True, reward_clip=True)
```

Important behavior:

- Random actions are used until `step_counter < explore_steps` is false.
- After warmup, the Actor uses ASL `Q_Net` on batches shaped like
  `[train_envs, 4, 84, 84]` and chooses greedy actions with per-environment
  exploration replacement.
- The vectorized exploration fraction linearly decays from
  `init_explore_frac` to `end_explore_frac`; `min_eps` is added to every
  environment probability.
- The Actor updates `total_steps` by `train_envs` each vectorized step.
- With time feedback enabled, the Actor stores mean vector-step time in `t[0]`
  and waits when it is faster than the Learner's scaled time.

## Learner role

The Learner builds an ASL `Q_Net`, uploads initial parameters, deep-copies a
frozen target net, and optimizes with Adam.

DQN/DDQN target behavior:

- `--DDQN True`: choose `argmax_a` with the online network, gather target Q from
  the target network.
- `--DDQN False`: use the max target Q directly.
- `dw` masks terminal transitions.
- `ct` marks whether state and next state are from a consistent trajectory;
  inconsistent samples are zeroed out in the loss.

Coordination:

- Every `upload_freq` backprop steps, Learner uploads parameters and asks Actor
  to download them.
- Every `hard_update_freq` backprop steps, Learner hard-updates target network
  and decays LR.
- Every `eval_freq` backprop steps, Learner queues a CPU state dict with steps
  and wall time for Evaluator processes.
- With time feedback enabled, Learner stores scaled learner time in `t[1]` and
  waits when it is faster than the Actor.

## Evaluator and Recorder roles

Evaluator behavior:

- Creates EnvPool evaluation environments with `episodic_life=False` and
  `reward_clip=False`.
- Consumes model snapshots from `shared_data.get_eval_model()`.
- Runs evaluation until every vectorized evaluation env is done.
- Appends `[score, steps, walltime]` to the shared curve.

Recorder behavior:

- Polls every 60 seconds.
- Copies and clears the shared curve.
- Sorts points by step before writing TensorBoard scalar `ep_r`.

## Sharer and shared-data device placement

ASL chooses the shared-data implementation from `--B_dvc`:

| `--B_dvc` value | Class | Storage | Constraint |
|---|---|---|---|
| `cpu` | `shared_data_cpu` | replay tensors live in RAM and sampled batches move to `--L_dvc` | Works with CPU or CUDA Learner |
| anything else | `shared_data_cuda` | replay tensors live on `--B_dvc` | `--B_dvc` must equal `--L_dvc` |

Replay tensor shapes are based on `(4, 84, 84)` observations:

```text
s, next_s: [buffersize/train_envs, train_envs, 4, 84, 84] uint8
a:         [buffersize/train_envs, train_envs, 1] int64
r:         [buffersize/train_envs, train_envs, 1]
dw, ct:    [buffersize/train_envs, train_envs, 1] bool
```

`shared_data_cpu.sample_core()` samples a time index and environment index,
returns `s, a, r, s_next, dw, ct`, and transfers batches to the learner device.
The CUDA variant generates sample indices on the buffer device and returns
already-device-resident batches.

## ASL command recipes

Real ASL commands must be run intentionally from the ASL workflow directory of a
DRL-Pytorch checkout. They create EnvPool environments and start worker
processes.

```bash
cd <repo-root>/6. Actor-Sharer-Learner
```

Default Alien DDQN ASL training, intended for a CUDA host with EnvPool and
Atari support:

```bash
python main.py
```

Pong ASL training with CPU devices and fewer train envs for debugging. This is
still not a tiny smoke because it launches EnvPool and processes.

```bash
python main.py --EnvIdex 37 --A_dvc cpu --B_dvc cpu --L_dvc cpu --E_dvc cpu --train_envs 8 --eval_envs 1 --max_train_steps 200000 --explore_steps 10000 --buffersize 20000
```

Enduro ASL with DDQN disabled, showing the DQN target switch:

```bash
python main.py --EnvIdex 20 --DDQN False --A_dvc cuda:0 --B_dvc cpu --L_dvc cuda:0 --E_dvc cuda:0
```

GPU replay-buffer mode requires matching buffer and learner devices:

```bash
python main.py --B_dvc cuda:0 --L_dvc cuda:0 --A_dvc cuda:0 --E_dvc cuda:0
```

Do not use `--B_dvc cuda:0 --L_dvc cuda:1`; the launcher asserts that a CUDA
buffer must share the Learner device.

## ASL module caveats

- ASL has its own `utils.py`, `Q_Net`, `LinearSchedule`, and `AtariNames.py`;
  do not mix them with the Atari DQN workflow's modules in one import path.
- The ASL `Q_Net` is a non-dueling convolutional DQN with hidden width
  `--fc_width` and output `action_dim`.
- `utils.str2bool` handles normal true/false strings. Invalid boolean strings
  are intended to raise an argparse error; avoid unusual values such as
  `--time_feedback maybe`.
- `buffersize` must be at least `explore_steps`; the launcher asserts this
  before process startup.
