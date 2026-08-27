# Training and Evaluation Workflows

## When to read

Read this when a task asks for training commands, evaluation/checkpoint playback, log artifacts, or recommended algorithm settings.

## Entry points and side effects

The repository's primary training script parses options equivalent to `main.py --help` and then:

1. Seeds PyTorch and optional CUDA determinism.
2. Cleans monitor CSV files in `--log-dir` and the derived evaluation directory `log_dir + "_eval"`.
3. Builds vectorized Gym environments with `make_vec_envs`.
4. Builds a `Policy` from the environment observation/action spaces.
5. Selects `A2C_ACKTR` for `--algo a2c`, `PPO` for `--algo ppo`, and `A2C_ACKTR(..., acktr=True)` for `--algo acktr`.
6. Collects rollouts, computes returns, updates the agent, saves checkpoints, and optionally evaluates.

Training is intentionally long-running. Do not use a full training command as a smoke test; use CLI help, the command builder, or the model-component smoke script instead.

## Core flags

| Flag | Default / values | Use |
| --- | --- | --- |
| `--algo` | `a2c`; choices `a2c`, `ppo`, `acktr` | Selects optimizer/update rule. |
| `--env-name` | `PongNoFrameskip-v4` | Gym id; DeepMind Control Suite uses `dm.<domain>.<task>`. |
| `--num-env-steps` | `10e6` | Total environment steps; reduce for smoke/trial runs. |
| `--num-processes` | `16` | Parallel env processes; PPO mini-batch constraints depend on this and `--num-steps`. |
| `--num-steps` | `5` | Rollout length before update; PPO examples use larger values. |
| `--use-gae`, `--gae-lambda` | false, `0.95` | Generalized advantage estimation. Use `--gae-lambda`, not stale `--tau`. |
| `--use-linear-lr-decay` | false | Linearly decays learning rate across updates. |
| `--use-proper-time-limits` | false | Handles time-limit truncation through `bad_masks`; recommended for MuJoCo-style control. |
| `--no-cuda` | false | Forces CPU even if CUDA is visible. |
| `--save-dir` | `./trained_models/` | Saves checkpoints under `<save-dir>/<algo>/<env-name>.pt`. |
| `--log-dir` | parser default temporary Gym log directory | Monitor CSV/log directory; existing `*.monitor.csv` files are removed. |
| `--eval-interval` | unset | When set and rewards exist, runs deterministic evaluation using `evaluation.evaluate`. |

## Recommended command families

### A2C basic Atari-style run

```bash
python main.py --env-name PongNoFrameskip-v4
```

### PPO Atari hyperparameters

```bash
python main.py --env-name PongNoFrameskip-v4 \
  --algo ppo --use-gae --lr 2.5e-4 --clip-param 0.1 \
  --value-loss-coef 0.5 --num-processes 8 --num-steps 128 \
  --num-mini-batch 4 --log-interval 1 --use-linear-lr-decay \
  --entropy-coef 0.01
```

### ACKTR Atari pattern

```bash
python main.py --env-name PongNoFrameskip-v4 \
  --algo acktr --num-processes 32 --num-steps 20
```

### PPO continuous-control pattern

```bash
python main.py --env-name Reacher-v2 \
  --algo ppo --use-gae --log-interval 1 --num-steps 2048 \
  --num-processes 1 --lr 3e-4 --entropy-coef 0 \
  --value-loss-coef 0.5 --ppo-epoch 10 --num-mini-batch 32 \
  --gamma 0.99 --gae-lambda 0.95 --num-env-steps 1000000 \
  --use-linear-lr-decay --use-proper-time-limits
```

Use `--no-cuda` when debugging CPU behavior or when CUDA dependencies are not configured.

## Evaluation and playback

Training saves a checkpoint tuple:

```text
[actor_critic, obs_rms]
```

The checkpoint path is:

```text
<save-dir>/<algo>/<env-name>.pt
```

The playback script expects `--load-dir` to point at the algorithm subdirectory and loads `<load-dir>/<env-name>.pt`. For example, if training used the default save dir and `--algo ppo`, playback would use:

```bash
python enjoy.py --load-dir trained_models/ppo --env-name Reacher-v2
```

`enjoy.py` renders in an infinite loop when a render function is available. Use it only for interactive playback, not automated verification.

## Batch experiment helpers

The repository includes evidence of multi-seed tmux command generation, but the generated commands can contain stale `--tau 0.95`. The current parser accepts `--gae-lambda 0.95`; replace `--tau` before running old templates.

Prefer [../scripts/build_training_command.py](../scripts/build_training_command.py) for safe command construction because it emits current parser flags and never launches training.
