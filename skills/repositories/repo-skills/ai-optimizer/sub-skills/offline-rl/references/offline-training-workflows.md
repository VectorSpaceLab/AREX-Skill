# Offline training workflows

This reference summarizes command surfaces and script behavior for the offline RL algorithms in this sub-skill. The command recipes are intentionally static. They describe how a target AI-Optimizer checkout's training scripts are invoked; they do not prove that a local simulator, D4RL dataset, GPU, or benchmark is available.

Use `scripts/build_offline_rl_command.py` to generate shell-quoted recipes instead of hand-composing commands.

## Flag families

| Algorithms | Selector flag | Seed flag | GPU flag | Notes |
| --- | --- | --- | --- | --- |
| BCQ, BEAR, CQL, AWAC | `--dataset` | `--seed` | `--gpu` integer | d3rlpy dataset loader returns `(dataset, env)`; scripts split episodes for evaluation and log to algorithm-specific tensorboard/log directories. |
| MOPO | `--dataset` | `--seed` | `--gpu` integer | Fits a probabilistic ensemble dynamics model, then trains the policy using model rollouts. |
| COMBO | `--dataset` | `--seed` | `--gpu` integer plus `--n_critics` | Use the COMBO-specific entry recipe when the goal is COMBO; the generic COMBO folder main recipe behaves like a MOPO-style path. |
| REDQ | `--env` | `--seed` | `--gpu` boolean-like value | Creates Gym envs and runs online `fit_online_redq` with a replay buffer; not a static D4RL-dataset-only recipe. |
| ISPI | `--env` | `--seed` | no explicit flag | Uses D4RL q-learning dataset conversion internally and chooses CUDA automatically when available. |
| UWAC | documented `--dataset` | `--seed` | `--gpu` integer | Algorithm class exists; some checkouts may lack a UWAC trainer file. Treat generated UWAC commands as a starting point requiring target-checkout confirmation. |

## Command recipe catalog

The examples below assume the target checkout layout has the corresponding algorithm scripts and that the command is launched from a location where the relative script path resolves.

### BCQ

Purpose: policy-constraint continuous-control offline RL using a behavior-model action constraint.

Recipe shape:

```bash
python offline-rl-algorithms/BCQ/bcq-train.py --dataset halfcheetah-medium-v2 --seed 0 --gpu 0
```

Important script facts:

- Loads `dataset, env = d3rlpy.datasets.get_dataset(dataset_name)`.
- Seeds d3rlpy and the Gym/D4RL env.
- Uses vector encoders with larger VAE/behavior and RL networks.
- Calls `BCQ.fit(dataset.episodes, eval_episodes=..., n_steps=1000000, n_steps_per_epoch=1000, save_interval=10, tensorboard_dir=...)`.

### BEAR

Purpose: policy-constraint offline RL using MMD support matching.

Recipe shape:

```bash
python offline-rl-algorithms/BEAR/bear-train.py --dataset halfcheetah-expert-v0 --seed 0 --gpu 0
```

Important script facts:

- Loads d3rlpy dataset and env, splits held-out episodes.
- Uses a VAE encoder and BEAR constructor values such as low actor learning rate, `alpha_threshold`, MMD action sampling, and `warmup_steps` defaults from the class.
- Logs under a generic `runs` style directory.

### CQL

Purpose: conservative Q-learning value regularization.

Recipe shape:

```bash
python offline-rl-algorithms/CQL/cql-train.py --dataset halfcheetah-random-v2 --seed 0 --gpu 0
```

Important script facts:

- Uses a three-layer vector encoder.
- Calls `CQL.fit` for one million steps with environment scorer and conservative value monitoring.
- CQL README content is sparse, so prefer script evidence and d3rlpy-derived API signatures.

### AWAC

Purpose: offline-to-online-oriented advantage-weighted actor critic; can be used as an offline warm start.

Recipe shape:

```bash
python offline-rl-algorithms/AWAC/awac-train.py --dataset halfcheetah-medium-v2 --seed 0 --gpu 0
```

Important script facts:

- Uses a four-layer vector encoder, Adam weight decay, batch size 1024, `lam=1.0`, and one million offline fit steps.
- Logs under an AWAC-specific tensorboard directory and uses environment evaluation scorer.

### REDQ

Purpose: randomized ensembled double Q-learning. In this collection the exposed trainer is an online Gym replay-buffer script, not a pure offline D4RL command.

Recipe shape:

```bash
python offline-rl-algorithms/REDQ/redq-train.py --env HalfCheetah-v2 --seed 1 --gpu False
```

Important script facts:

- The script uses `--env`, not `--dataset`.
- It creates training and evaluation Gym environments, builds a d3rlpy `REDQ`, creates an online replay buffer, and calls `fit_online_redq`.
- Treat README examples that look dataset-like as less authoritative than the script's parser.

### UWAC

Purpose: uncertainty weighted actor critic, based on a BEAR/SAC-style constrained actor with uncertainty-weighted critic loss.

Recipe shape when a target trainer exists:

```bash
python offline-rl-algorithms/UWAC/uwac-train.py --dataset walker2d-random-v2 --seed 0 --gpu 0
```

Important script facts:

- The algorithm class exposes BEAR-like MMD, VAE, alpha, temperature, and dropout/uncertainty parameters.
- Some checkouts expose the class but not the train-file advertised by lightweight docs. If the trainer is absent, instantiate the class through the d3rlpy-style API instead of running a missing script.

### ISPI

Purpose: standalone offline RL script with pessimistic actor updates and D4RL q-learning dataset conversion.

Recipe shape:

```bash
python offline-rl-algorithms/ISPI/main.py --policy ISPI --env hopper-medium-v2 --seed 0 --eval_freq 5000 --max_timesteps 1000000 --eval_episodes 10
```

Useful flags:

- `--normalize` enables state normalization.
- `--reward_scale`, `--reward_bias`, and `--reward_standardize` control reward preprocessing.
- `--save_model`, `--save_freq`, and `--load_model` control checkpoint behavior.
- There is no explicit `--gpu`; the script chooses CUDA if available.

### MOPO

Purpose: model-based offline policy optimization.

Recipe shape:

```bash
python offline-rl-algorithms/MOPO/main.py --dataset hopper-medium-v0 --seed 1 --gpu 0
```

Important script facts:

- Requires D4RL/MuJoCo-style environments and a d3rlpy dynamics stack.
- Fits a `ProbabilisticEnsembleDynamics` model before policy training.
- Uses per-dataset rollout horizon and penalty parameters where known; defaults are used otherwise.
- Runtime is much heavier than PC/VR command construction.

### COMBO

Purpose: conservative offline model-based policy optimization.

Recipe shape:

```bash
python offline-rl-algorithms/COMBO/combo_main.py --dataset hopper-medium-v2 --seed 1 --n_critics 2 --gpu 0
```

Important script facts:

- Fits a probabilistic ensemble dynamics model first.
- Sets conservative weight heuristically from the dataset name.
- Uses lower actor/critic learning rates and shorter rollout horizon on Walker2d-style datasets.
- Requires static termination functions matching the environment family.

## When to avoid executing

Avoid launching the generated commands until the task explicitly approves heavyweight work and confirms all prerequisites. The commands can run for hundreds of thousands to millions of steps, may write checkpoints/logs, and may fail early if MuJoCo, D4RL, Gym versions, CUDA, or dataset downloads are missing.
