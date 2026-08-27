# Training workflows

This reference is self-contained operating guidance for `rl_zoo3` training commands. It assumes RL Zoo is installed as a Python package named `rl_zoo3`.

## Command entry points

Prefer the installed module entry point for training:

```bash
python -m rl_zoo3.train --algo ppo --env CartPole-v1
```

The console router is equivalent for training when its optional imports are available:

```bash
rl_zoo3 train --algo ppo --env CartPole-v1
```

Use the module form for base installs or when `rl_zoo3 train --help` fails due plotting extras. Use the console form when a workflow standardizes on `rl_zoo3 <subcommand>` and its imports are known to work.

## Training lifecycle used by RL Zoo

A training command performs these steps:

1. Parse CLI flags, import modules named by `--gym-packages`, then verify `--env` is present in the Gymnasium registry. On failure it raises a closest-match error.
2. Choose or generate a seed. If `--seed` is negative or omitted, RL Zoo samples a random seed. Positive seeds are passed to Stable-Baselines3 and environment creation.
3. Optionally set PyTorch thread count with `--num-threads`.
4. Assert `--trained-agent` is an existing `.zip` file when continuation is requested.
5. Build an `ExperimentManager` with algorithm, environment, log folder, config path, CLI overrides, eval/checkpoint/replay/tracking/device options, and vectorized-env type.
6. Load hyperparameters from the selected algorithm config, custom YAML/Python config, or Python module. Environment-specific entries take priority; Atari entries and `default` fallback are used when applicable.
7. Preprocess common config keys: schedules, `n_envs`, `n_timesteps`, normalization, policy kwargs, action noise, wrappers, vector wrappers, callbacks, and monitor kwargs.
8. Create the training environment with Gymnasium `spec.make`, `make_vec_env`, `--env-kwargs`, Monitor logging, selected `--vec-env`, wrappers, optional normalization, frame stacking, and image transposition.
9. Create callbacks:
   - progress bar when `--progress` / `-P` is set;
   - checkpoints when `--save-freq > 0`;
   - evaluation and best-model saving when `--eval-freq > 0` and not optimizing.
10. Either instantiate a fresh model from the `ALGOS` registry or load `--trained-agent` and, if present, the adjacent `replay_buffer.pkl`.
11. Run `model.learn(...)`, save the final model, save `replay_buffer.pkl` when requested and supported, and save `VecNormalize` stats when normalization is enabled.

## Output layout

With `--log-folder ./runs/rl-zoo --algo sac --env Pendulum-v1`, the default output has this shape:

```text
./runs/rl-zoo/
  sac/
    Pendulum-v1_1/
      Pendulum-v1.zip                  # final saved model
      replay_buffer.pkl                # only when supported and --save-replay-buffer was set
      best_model.zip                   # when evaluation callback improves best reward
      evaluations.npz                  # when evaluation callback is active
      rl_model_<steps>_steps.zip       # when checkpoint callback is active
      *.monitor.csv                    # Monitor episode statistics for training envs
      Pendulum-v1/
        args.yml                       # sorted CLI arguments
        config.yml                     # saved hyperparameters before preprocessing
        command.txt                    # command used for the run
        vecnormalize.pkl               # only when normalization is enabled
```

Run ids are monotonic per `log_folder/algo/env_id_*`. `--uuid` appends a UUID suffix to the run folder to avoid races in parallel launches. Continuing training creates a new run folder for the resumed output; it does not overwrite the zip passed by `--trained-agent`.

## Bounded smoke training

Use a CPU smoke run before any long experiment:

```bash
python -m rl_zoo3.train --algo ppo --env CartPole-v1 \
  --n-timesteps 1000 --log-folder ./runs/rl-zoo-smoke \
  --eval-freq 500 --eval-episodes 2 --save-freq 500 \
  --seed 123 --device cpu --progress
```

Notes:

- `CartPole-v1` is a safe classic-control environment for PPO/A2C/DQN-style smoke checks.
- Use `Pendulum-v1` for continuous-control off-policy algos such as SAC/TD3/DDPG/TQC/CrossQ.
- `--progress` uses tqdm/rich and is safe when those base dependencies are installed; omit it in non-interactive logs if it makes output noisy.

## Full training run safety

For a long run, do not omit planning flags:

```bash
python -m rl_zoo3.train --algo sac --env Pendulum-v1 \
  --log-folder ./runs/rl-zoo-sac --n-timesteps 20000 \
  --eval-freq 5000 --eval-episodes 5 --n-eval-envs 1 \
  --save-freq 5000 --save-replay-buffer --seed 2025 \
  --device auto --uuid
```

Safety checklist:

- Choose a dedicated log folder.
- Keep `--n-timesteps` explicit unless intentionally using the config default, which can be large.
- Save checkpoints often enough to survive interruption.
- For off-policy algorithms, add `--save-replay-buffer` when later continuation should preserve sample history.
- Use `--device cpu` for portability or `--device cuda` only when accelerator availability is established.
- Use `--uuid` for concurrent runs writing under the same log root.

## Continuing from a trained agent zip

Continuation requires an existing model zip:

```bash
python -m rl_zoo3.train --algo a2c --env CartPole-v1 \
  --trained-agent ./runs/rl-zoo/a2c/CartPole-v1_1/CartPole-v1.zip \
  --n-timesteps 5000 --log-folder ./runs/rl-zoo \
  --eval-freq 1000 --save-freq 1000 --seed 123 --device cpu
```

Behavior:

- The zip path must end in `.zip` and exist before launch.
- Policy and `policy_kwargs` from the current config are removed before loading the pretrained agent so the saved policy definition remains authoritative.
- Normalization stats are loaded from a `vecnormalize.pkl` under the model's environment subfolder when present.
- Resumed outputs go to the next run id under the selected `--log-folder`.

## Off-policy replay-buffer continuation

RL Zoo automatically attempts to load `replay_buffer.pkl` located next to the `--trained-agent` zip. Save it during the initial run and again after the resumed run if needed.

Initial SAC run:

```bash
python -m rl_zoo3.train --algo sac --env Pendulum-v1 \
  --n-timesteps 1000 --log-folder ./runs/sac-buffer \
  --save-replay-buffer --eval-freq 500 --save-freq 500 \
  --hyperparams buffer_size:1000 --env-kwargs g:8.0 \
  --eval-env-kwargs g:5.0 --seed 7 --device cpu
```

Continuation with the adjacent replay buffer:

```bash
python -m rl_zoo3.train --algo sac --env Pendulum-v1 \
  --trained-agent ./runs/sac-buffer/sac/Pendulum-v1_1/Pendulum-v1.zip \
  --n-timesteps 1000 --log-folder ./runs/sac-buffer \
  --save-replay-buffer --eval-freq 500 --save-freq 500 \
  --hyperparams buffer_size:1000 --env-kwargs g:8.0 \
  --eval-env-kwargs g:5.0 --seed 7 --device cpu
```

Key points:

- Replay-buffer save/load is meaningful for off-policy algorithms that implement replay buffers, such as `dqn`, `qrdqn`, `ddpg`, `sac`, `td3`, `tqc`, and `crossq`.
- If `replay_buffer.pkl` is absent, the model can still load, but replay history is not restored.
- For HER replay buffers, `--truncate-last-trajectory` controls the last trajectory on reload. The default is true; avoid passing a false-looking string unless you have verified the parser behavior in the target runtime.

## Evaluation and checkpoint frequency with `n_envs`

RL Zoo reads `n_envs` from config or `--hyperparams n_envs:<int>`. Positive frequencies are divided by `n_envs` before callback creation:

```text
effective_callback_frequency = max(requested_frequency // n_envs, 1)
```

Example:

```bash
python -m rl_zoo3.train --algo ppo --env CartPole-v1 \
  --n-timesteps 10000 --log-folder ./runs/ppo-nenvs \
  --hyperparams n_envs:8 --eval-freq 10000 --save-freq 50000
```

With `n_envs:8`, the evaluation callback is configured with `1250` environment-step calls. This preserves approximately the requested total-timestep spacing. Very small requested frequencies become `1` after the `max(..., 1)` guard.

## Vectorized environment choice

`--vec-env dummy` is the default and is often fastest/least memory-heavy. Use it for smoke tests and most small classic-control runs.

`--vec-env subproc` can help expensive environments but requires environment constructors, wrappers, and registration modules to be importable and pickleable in worker processes. If a custom env fails only with subprocess vectorization, retry with `--vec-env dummy` and then fix custom registration/import boundaries through `../../custom-components/SKILL.md`.

## Custom env modules and env kwargs

Registration modules listed with `--gym-packages` are imported before RL Zoo validates the env id:

```bash
python -m rl_zoo3.train --algo ppo --env MyEnv-v0 \
  --gym-packages my_env_package.registration \
  --conf-file my_package.my_config --n-timesteps 1000
```

Environment constructor kwargs use `key:python_expression` tokens:

```bash
python -m rl_zoo3.train --algo sac --env Pendulum-v1 \
  --env-kwargs g:8.0 --eval-env-kwargs g:5.0 \
  --n-timesteps 1000 --log-folder ./runs/sac-gravity
```

Use separate `--eval-env-kwargs` when evaluation should differ from training. If `--eval-env-kwargs` is omitted, evaluation kwargs default to the training `--env-kwargs`.

## Command builder helper

The bundled helper prints commands and performs common validation without importing RL Zoo or launching training:

```bash
python ../scripts/train_command_builder.py --algo sac --env Pendulum-v1 \
  --n-timesteps 1000 --log-folder ./runs/sac-buffer \
  --save-replay-buffer --hyperparams buffer_size:1000 \
  --env-kwargs g:8.0 --eval-env-kwargs g:5.0 \
  --trained-agent ./runs/sac-buffer/sac/Pendulum-v1_1/Pendulum-v1.zip \
  --allow-missing-files
```

Use `--command-style console` to produce `rl_zoo3 train ...`; otherwise the helper emits `python -m rl_zoo3.train ...`.
