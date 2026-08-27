# MBPO, ED2-MBPO, and BMPO Workflows

Use this reference for model-based policy optimization, short model rollout baselines, ED2-MBPO dynamics decomposition, and bidirectional model-based policy optimization.

## Family summary

| Variant | Role | Main evidence-backed command shape | Best-fit task |
|---|---|---|---|
| Vanilla MBPO | Model-Based Policy Optimization with short model-generated rollouts branched from real data | `mbpo run_local examples.development --config=examples.config.halfcheetah.0 --gpus=1 --trial-gpus=1` | Reproducing or adapting the NeurIPS 2019 continuous-control baseline. |
| ED2-MBPO | MBPO with ED2-style dynamics decomposition and action-group config | `python -u mbpo.py --config=examples.config.halfcheetah.0 --gpus=1 --trial-gpus=1 --cpus=1 --trial-cpus=1` | Comparing ED2 decomposition against MBPO under the same environment configs. |
| BMPO | Bidirectional Model-based Policy Optimization with forward and backward dynamics rollouts | README recipe: `python main.py --config=config.hopperNT` | Studying higher tolerance to model error via bidirectional rollouts. |

All three are old research-code workflows. Treat MuJoCo, old TensorFlow/Ray/Gym versions, GPU availability, and long training as prerequisites rather than verified facts.

## Vanilla MBPO

### Installation family

The README recipe expects:

1. MuJoCo 1.50 installed and licensed for `mujoco-py`.
2. Recursive MBPO checkout with its submodules.
3. A conda environment from `environment/gpu-env.yml`.
4. Editable installs of `viskit` and the MBPO package.

Do not treat a modern Gym/MuJoCo install as automatically compatible; this code belongs to the Gym 0.12 / MuJoCo 1.50 era.

### Run recipe

```bash
mbpo run_local examples.development --config=examples.config.halfcheetah.0 --gpus=1 --trial-gpus=1
```

Only local execution is documented. Logs are viewed with:

```bash
viskit ~/ray_mbpo --port 6008
```

### Config and extension points

| Surface | Purpose |
|---|---|
| environment config module, for example `examples.config.halfcheetah.0` | Select domain/task and algorithm hyperparameters. |
| `rollout_schedule` | Four-value schedule `[start_epoch, end_epoch, start_length, end_length]`; README example `[20, 100, 1, 5]`. |
| `model_train_freq` | Frequency for model updates. Increase/decrease to trade runtime against model freshness. |
| `max_model_t` | Optional timeout for model training in seconds. |
| static termination function | Required for a new environment; name it consistently with the lowercase environment/domain name. |
| `log_dir` | Default points to a Ray/viskit log root. Keep result paths consistent across runs. |

## ED2-MBPO

### Installation family

ED2-MBPO tells users to follow the MBPO installation stack: MuJoCo 1.50, GPU conda environment, editable package install, and the MBPO/softlearning dependencies.

The environment requirements evidence includes old pins such as TensorFlow GPU 1.13.1, TensorFlow Probability 0.6.0, Ray 0.6.4, Gym 0.12.0, gpflow 1.4.1, mujoco-py from a Git URL, and several 2018-era scientific Python packages.

### Run recipe

The README says:

```bash
python run.py
```

The inspected launcher builds five background commands for GPUs `0..4`, fixed task `halfcheetah`, and model `0`. A safer single-command equivalent is:

```bash
CUDA_VISIBLE_DEVICES=0 python -u mbpo.py --config=examples.config.halfcheetah.0 --gpus=1 --trial-gpus=1 --cpus=1 --trial-cpus=1
```

Do not run the multi-GPU launcher without explicit resource approval; it writes logs under `log_files/<task>/<model>/` and backgrounds processes.

### Config facts

The visible ED2-MBPO configs cover `halfcheetah`, `hopper`, `walker2d`, and `ant`, each with a `0.py` module. A representative config contains:

- `type='MBPO'`, `universe='gym'`, domain/task fields such as `HalfCheetah` and `v2`.
- `exp_name='ED2'`, `log_dir='~/ray_mbpo/'`.
- SAC/model-based hyperparameters: `epoch_length`, `n_train_repeat`, `model_train_freq`, `model_retain_epochs`, `rollout_batch_size`, `num_networks`, `num_elites`, `real_ratio`, `target_entropy`, `max_model_t`.
- ED2-specific decomposition surface such as `hidden_dim` and `action_group`, for example grouped action indexes for HalfCheetah.

## BMPO

### Dependency family

BMPO requirements evidence pins:

- `mujoco-py==1.50.1.68`
- `tensorflow-gpu==1.13.1`
- `tensorflow-probability==0.6.0`
- `ray[rllib,debug]==0.6.4`
- `gym==0.12.0`
- `gtimer==1.0.0b5`
- a Git dependency on `serializable`

These pins are sensitive to Python, CUDA, and system MuJoCo versions.

### Run recipe and launcher caveat

The README recipe is:

```bash
python main.py --config=config.hopperNT
```

However, the inspected checkout evidence shows `runner.py`, `bmpo.py`, config modules, static termination functions, and environment wrappers, but no visible `main.py` in the BMPO directory. Before running BMPO, verify whether the target runtime has a missing launcher, or create a small launcher that imports the requested `config.<name>.params`, constructs `ExperimentRunner`, and calls `train()`.

### Config facts

BMPO config modules include names such as `hopper`, `hopperNT`, `walker2d`, `walker2dNT`, `ant`, and `pendulum`. Representative fields include:

| Config field | Meaning |
|---|---|
| `type='BMPO'` | Selects the BMPO algorithm. |
| `universe`, `domain`, `task` | Softlearning/Gym environment selector, for example `HopperNT` + `v2`. |
| `log_dir`, `exp_name` | Logging identity. Runtime also writes per-domain logs under `./log/<domain>/`. |
| `model_train_freq`, `model_retain_epochs`, `rollout_batch_size` | Dynamics-model update cadence and synthetic data retention. |
| `num_networks`, `num_elites` | Ensemble size and elite model count. |
| `forward_rollout_schedule`, `backward_rollout_schedule` | Four-value schedules controlling forward and backward model rollout length. |
| `beta_schedule` | Sampling schedule used by the bidirectional rollout logic. |
| `planning_horizon`, `backward_policy_var`, `last_n_epoch` | BMPO-specific planning/backward-policy controls. |

### Runner behavior facts

The `ExperimentRunner` builds training/evaluation environments, replay pool, sampler, Q-functions, policy, and an initial uniform exploration policy using softlearning utilities. It resolves static termination functions by lowercasing the training domain, creates `./log/<domain>/` if missing, initializes TensorFlow variables, and then calls the BMPO algorithm's `train()` method.

## Choosing MBPO versus BMPO

| User intent | Route |
|---|---|
| Vanilla model-based policy optimization baseline | Vanilla MBPO. |
| ED2 comparison with action-group decomposition | ED2-MBPO. |
| Forward/backward model rollouts or tolerance to model error | BMPO. |
| Pixel world-model/control task | Dreamer or PlaNet instead. |
| Offline model-based algorithms COMBO/MOPO | Route to `offline-rl`; those are offline RL workflows, not this online MBRL route. |

## Safe validation before heavy runs

- Validate that the intended Python can import old TensorFlow/Ray/Gym/MuJoCo pins before starting training.
- Confirm MuJoCo license/runtime compatibility with `mujoco-py==1.50.1.68`.
- Inspect or generate the exact config module name; config import failures are common when a command's dotted module path and working directory differ.
- Prefer a single foreground command over `nohup`/background loops during first validation.
- Record log/result roots before running because defaults such as `~/ray_mbpo/`, `log_files/...`, and `./log/<domain>/` can scatter outputs.
