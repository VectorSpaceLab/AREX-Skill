# CLI and config composition

This reference distills the DreamerV3 startup path in `dreamerv3/main.py` and the preset tree in `dreamerv3/configs.yaml`.
It is the main place to check when you need to choose flags, compose presets, or understand which config keys affect a training run.

## How startup builds the runtime config

`main()` follows this order:

1. load `configs.yaml`
2. parse `--configs` against `defaults`
3. merge each named config block in the order it was listed
4. parse the remaining CLI flags into the merged config
5. format `logdir` with the current timestamp placeholder
6. if `JOB_COMPLETION_INDEX` is set, override `replica`
7. create the logdir and save `config.yaml` unless the script ends in `_env` or `_replay`
8. set up `portal`
9. dispatch to the selected run loop via `config.script`

### Override semantics

- Later `--configs` blocks override earlier ones.
- Explicit CLI flags override every preset block.
- This means `--configs debug multicpu --batch_size 1` starts from `defaults`, applies `debug`, then applies `multicpu`, then forces `batch_size=1`.
- The smoke helper in this sub-skill uses the same pattern.

## Core config areas

| Area | Key examples | What they control |
| --- | --- | --- |
| top-level | `logdir`, `replica`, `replicas`, `method`, `task`, `seed`, `script`, `batch_size`, `batch_length`, `report_length`, `replay_context`, `random_agent` | Run identity, task choice, smoke size, and agent selection |
| logger | `logger.outputs`, `logger.filter`, `logger.timer`, `logger.fps`, `logger.user` | Terminal, JSONL, Scope, TensorBoard, WandB, or Expa logging |
| run | `run.steps`, `run.train_ratio`, `run.log_every`, `run.report_every`, `run.save_every`, `run.envs`, `run.eval_envs`, `run.eval_eps`, `run.from_checkpoint`, `run.from_checkpoint_regex`, `run.debug`, `run.actor_batch`, `run.remote_envs`, `run.remote_replay`, `run.agent_process` | Loop cadence, evaluation cadence, resume behavior, and parallel launch shape |
| jax | `jax.platform`, `jax.compute_dtype`, `jax.prealloc`, `jax.debug`, `jax.mock_devices`, `jax.policy_devices`, `jax.train_devices` | CPU/GPU/TPU placement and debug behavior |
| agent | `agent.*` | Dreamer network and optimization shape |
| env | `env.<suite>.*` | Suite-specific environment settings |
| replay | `replay.size`, `replay.online`, `replay.fracs.*`, `replay.prio.*`, `replay.recexp`, `replay.chunksize` | Replay capacity and selector behavior |

## Important config blocks

### Size presets

These blocks only reshape the model and related heads:

| Preset | Effect | Resume safety |
| --- | --- | --- |
| `size1m` | Smaller RSSM, depth, and width | Do not reuse a checkpoint from a different size preset unless compatibility is known |
| `size12m` | Mid-size network | Same caution |
| `size25m` | Larger network | Same caution |
| `size50m` | Larger network | Same caution |
| `size100m` | Larger network | Same caution |
| `size200m` | Default-scale large network | Same caution |
| `size400m` | Largest preset in this tree | Same caution |

### Task presets

| Preset | Task | Run overrides |
| --- | --- | --- |
| `minecraft` | `minecraft_diamond` | none |
| `dmlab` | `dmlab_explore_goal_locations_small` | `steps=2.6e7`, `train_ratio=32` |
| `atari` | `atari_pong` | `steps=5.1e7`, `train_ratio=32` |
| `procgen` | `procgen_coinrun` | `steps=1.1e8`, `train_ratio=64` |
| `atari100k` | `atari100k_pong` | `steps=1.1e5`, `envs=1`, `train_ratio=256` |
| `crafter` | `crafter_reward` | `steps=1.1e6`, `envs=1`, `train_ratio=512` |
| `dmc_proprio` | `dmc_walker_walk` | `size1m`, `env.dmc.image=False`, `steps=1.1e6`, `train_ratio=1024` |
| `dmc_vision` | `dmc_walker_walk` | `env.dmc.proprio=False`, `steps=1.1e6`, `train_ratio=256` |
| `bsuite` | `bsuite_mnist/0` | `envs=1`, `save_every=-1`, `train_ratio=1024` |
| `loconav` | `loconav_ant_maze_m` | `env.loconav.repeat=1`, `train_ratio=256` |

### Debug and multicpu

| Preset | Effect |
| --- | --- |
| `debug` | CPU platform, small batch sizes, tiny model, short log/report/save intervals, smaller replay size, fewer envs |
| `multicpu` | Simulated multi-device layout with mock devices and explicit policy/train device splits |

## `main.py` helper contracts

| Function | Contract | Key inputs | Typical failure if wrong |
| --- | --- | --- | --- |
| `main` | Build the final config, save `config.yaml`, set up `portal`, and dispatch to the chosen run loop | `logdir`, `script`, `run.*`, `jax.*`, `logger.*` | Invalid script name, missing task, or wrong config composition |
| `make_agent` | Infer obs/act spaces from env 0, then create either `RandomAgent` or the Dreamer agent | `task`, `random_agent`, `agent.*`, `jax.*`, `batch_size`, `batch_length`, `replay_context`, `report_length` | Env creation failure or incompatible agent config |
| `make_env` | Split `task` into suite/task, select the suite constructor, apply suite config, and wrap the env | `task`, `env.<suite>.*`, `seed`, `logdir` | Unsupported suite prefix or missing optional env dependency |
| `make_replay` | Size replay, configure selector mixture, and validate capacity against the requested batch length | `replay.*`, `batch_size`, `batch_length`, `report_length`, `consec_train`, `consec_report`, `replay_context`, `jax.compute_dtype` | Capacity assertion or incompatible low-precision prioritized replay |
| `make_stream` | Wrap replay sampling with consecutive segment handling | `batch_length`, `report_length`, `consec_train`, `consec_report`, `replay_context` | Sampling shapes do not match the run loop |
| `make_logger` | Create terminal, JSONL, Scope, TensorBoard, WandB, or Expa outputs | `logger.outputs`, `logger.filter`, `logger.timer`, `logger.fps`, `logdir` | Missing output backend or wrong logdir expectation |

## Logger output map

| Output | Effect |
| --- | --- |
| `jsonl` | Writes `metrics.jsonl` and `scores.jsonl` |
| `scope` | Writes Scope summaries under the logdir |
| `tensorboard` | Writes TensorBoard event files |
| `wandb` | Uses the logdir path tail as the run name |
| `expa` | Uses the logdir path tail and configured user/project metadata |

The default logger stack is terminal + JSONL + Scope.

## Safe command recipes

### CPU debug smoke

```sh
python -m dreamerv3.main \
  --configs debug \
  --task dummy_disc \
  --jax.platform cpu \
  --logdir ~/logdir/dreamer/debug/{timestamp} \
  --run.steps 16 \
  --run.train_ratio 1 \
  --run.envs 1
```

Why this is safe:

- dummy env avoids suite-specific optional dependencies
- CPU avoids accelerator setup
- `debug` shrinks the model and runtime intervals
- `run.steps` stays tiny
- `run.train_ratio=1` keeps the smoke bounded
- `envs=1` avoids multiprocess fanout

### Random-agent smoke

```sh
python -m dreamerv3.main \
  --configs debug \
  --task dummy_disc \
  --random_agent True \
  --jax.platform cpu \
  --logdir ~/logdir/dreamer/debug-random/{timestamp} \
  --run.steps 16 \
  --run.train_ratio 1 \
  --run.envs 1
```

Use this when you want to check env, replay, logger, and checkpoint plumbing without exercising Dreamer model training.

### Resume from an existing logdir

```sh
python -m dreamerv3.main \
  --configs debug \
  --task dummy_disc \
  --jax.platform cpu \
  --logdir ~/logdir/dreamer/debug/{timestamp} \
  --run.steps 100 \
  --run.train_ratio 1 \
  --run.envs 1
```

To continue a stopped run, rerun the same command with the same `--logdir`.
If you changed a size preset or other shape-sensitive config, use a fresh logdir instead.

### Resume from another checkpoint

```sh
python -m dreamerv3.main \
  --configs debug \
  --task dummy_disc \
  --jax.platform cpu \
  --logdir ~/logdir/dreamer/debug-resume/{timestamp} \
  --run.from_checkpoint /path/to/other/run/ckpt \
  --run.steps 100 \
  --run.train_ratio 1 \
  --run.envs 1
```

Only use this when the source checkpoint is shape-compatible with the current config.

## Output expectations

A successful non-parallel run usually creates:

- `logdir/config.yaml`
- `logdir/metrics.jsonl`
- `logdir/scores.jsonl`
- `logdir/ckpt/`

A healthy smoke should also print the replica, logdir, and selected script at startup.

## Quick decision guide

- Need the smallest validation possible: use the smoke helper with `dummy_disc` and `debug`.
- Need to compare a new size preset: use a fresh logdir.
- Need to inspect logs only: `jsonl` plus `scope` is enough.
- Need to resume from a checkpoint: keep the logdir stable and keep the model shape stable.
- Need to evaluate only: switch to the run-loop reference for `eval_only`.
