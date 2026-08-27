# Run-loop roles

This reference covers the operational roles of `embodied/run/train.py`, `train_eval.py`, `eval_only.py`, and `parallel.py` as wired by `dreamerv3/main.py`.
Use it to pick the right loop, understand checkpoint placement, and know which logs to expect.

## At a glance

| Mode | Main job | Best use | Checkpoint path |
| --- | --- | --- | --- |
| `train` | Single-process actor/learner with one replay and one logger | Default training and resume | `logdir/ckpt` |
| `train_eval` | Training plus a separate evaluation replay and evaluation env loop | Training with interleaved evaluation | `logdir/ckpt` |
| `eval_only` | Load a checkpoint and run evaluation only | Benchmarking or validation | no new training checkpoint writes |
| `parallel` | Multi-process / multi-thread combined actor, learner, replay, and logger | Distributed or multi-device execution | `logdir/ckpt/agent`, `logdir/ckpt/replay`, `logdir/ckpt/logger` |
| `parallel_env` | One environment worker | Environment-only worker shard | none |
| `parallel_envs` | Train + eval environment workers | Env farm without learner/replay | none |
| `parallel_replay` | Replay service only | Replay shard / remote replay setup | `logdir/ckpt/replay` |

## Shared runtime facts

- `step` is the shared global counter exposed through the logger.
- `run.steps` is the total number of environment steps to collect.
- `train_ratio` is converted into a training cadence relative to `batch_size * batch_length`.
- `run.debug` disables parallel `Driver` execution in the single-process loops.
- `logger.write()` flushes metrics on the configured cadence.
- `config.save_every` controls when checkpoint saves happen.
- `config.report_every` controls report / evaluation cadence.
- `config.log_every` controls metric flush cadence.

## `train`

### Role

The simplest training loop.
It creates:

- one agent
- one replay
- one logger
- one environment driver with `envs` envs

### Flow

1. build agent, replay, and logger
2. construct env drivers
3. sample the replay through the training and report streams
4. train while the replay is large enough
5. log metrics, replay stats, usage, and timer data
6. save checkpoints on schedule

### Checkpoint behavior

- `cp = elements.Checkpoint(logdir / 'ckpt')`
- `cp.step`, `cp.agent`, and `cp.replay` are stored
- `cp.load_or_save()` resumes if the checkpoint exists, otherwise creates one
- rerunning the same command with the same logdir is the normal continuation path

### Expected outputs

- `config.yaml`
- `metrics.jsonl`
- `scores.jsonl`
- `ckpt/`
- terminal `episode`, `replay`, `usage`, `fps`, and `timer` summaries

### Good smoke target

- `debug` + `dummy_disc` + CPU + `envs=1`
- optionally `random_agent=True` to isolate plumbing issues

## `train_eval`

### Role

Single-process training with a second evaluation environment set and a second replay.
Use it when you need training and evaluation in the same run without the complexity of the full parallel stack.

### What it adds over `train`

- `replay_train` and `replay_eval`
- `make_env_train` and `make_env_eval`
- a dedicated evaluation driver
- evaluation report logging under `eval` and `report`

### Flow details

- `Evaluation` is printed at report time.
- Evaluation envs run with `eval_policy`.
- Training continues between evaluation intervals.
- `should_save(step)` is called after the initial load-or-save so the schedule stays aligned.

### Checkpoint behavior

- checkpoint path is still `logdir/ckpt`
- both replay stores are checkpointed
- the same compatibility rule applies: keep the model shape stable if you want to reuse the logdir

### Expected outputs

- training metrics under `train/*`
- episode stats under `episode/*` and `epstats/*`
- evaluation metrics under `eval/*`
- `metrics.jsonl`, `scores.jsonl`, and `ckpt/`

## `eval_only`

### Role

Load an existing checkpoint and run only evaluation.
There is no training and no replay writeback.

### Required input

- `run.from_checkpoint` must be set

### Flow

1. build the agent
2. build the logger
3. create the env driver
4. load only the agent checkpoint
5. run the eval policy until `run.steps` is reached

### Checkpoint behavior

- `cp = elements.Checkpoint()`
- only `agent` is loaded
- no training checkpoint is created unless the logger or surrounding setup writes other files

### Expected outputs

- evaluation metrics and episode summaries
- `metrics.jsonl` and `scores.jsonl` if the configured logger outputs are enabled

## `parallel`

### Role

The combined distributed launcher.
It spawns the actor/learner, logger, env workers, and replay service as separate portal workers.

### Worker layout

- actor/learner worker: `parallel_agent`
- logger worker: `parallel_logger`
- env workers: `parallel_env`
- replay worker: `parallel_replay`

### Important launch rules

- if `actor_batch <= 0`, the launcher chooses `max(1, envs // 2)`
- `actor_batch` must not exceed `envs`
- `{auto}` placeholders in `actor_addr`, `replay_addr`, and `logger_addr` are expanded to free ports
- `agent_process` controls whether the agent runs in a process or thread
- `remote_envs` and `remote_replay` let you omit those worker groups from the local launch

### Checkpoint layout

- `ckpt/agent`
- `ckpt/replay`
- `ckpt/logger`

### Logging behavior

Parallel mode emits extra stats, including:

- `parallel/*`
- `server/*`
- `client/*`
- `usage/*`
- `fps/*`

### When to use

Use `parallel` when a single-process smoke is not enough and you need to verify the multi-worker control plane, remote replay, or device sharding assumptions.

## `parallel_env`

### Role

Start one environment worker shard.

### Use when

- you want to distribute environment stepping yourself
- you need to isolate an env worker failure
- you are assembling a custom portal deployment

### Notes

- no checkpoint is created here
- the worker still uses `make_env`
- `is_eval` is inferred from `replica` and `envs` when launched through the combined stack

## `parallel_envs`

### Role

Start the full set of train and eval environments without the learner or replay service.

### Use when

- the learner/replay live elsewhere
- you only want to validate environment fanout
- you are debugging environment-side dependency failures

## `parallel_replay`

### Role

Start only the replay and stream service.

### Use when

- replay is remote
- you want to isolate replay sizing, sampling, or checkpoint issues
- you are debugging train/report/eval sampling without the env workers

### Checkpoint layout

- `ckpt/replay`

## Resume and compatibility rules

- Continuing a stopped run normally means rerunning the same command with the same logdir.
- `run.from_checkpoint` is for loading from another checkpoint tree.
- Any change that alters tensor shapes or parameter counts can make a checkpoint incompatible.
- Size preset changes are the most common cause of checkpoint mismatch.
- If a resume fails with a PyTree or shape-related error, do not keep forcing the same logdir; use a new one or restore a compatible config.

## Debug-mode implications

The `debug` preset changes more than just the model size:

- CPU platform
- smaller batch and report sizes
- shorter logging intervals
- fewer envs
- smaller replay size

That makes it ideal for a smoke run, but not for meaningful learning curves.

## Artifact checklist by mode

| Mode | Minimum evidence that it is wired correctly |
| --- | --- |
| `train` | startup banner, logdir print, `config.yaml`, `ckpt/`, at least one metrics flush |
| `train_eval` | `Evaluation` printout, train metrics, eval metrics, checkpoint tree |
| `eval_only` | checkpoint load succeeds, eval metrics appear, no train updates |
| `parallel` | workers start, ports resolve, replay and logger stats appear, checkpoint subtrees exist |
| `parallel_envs` | env workers start without learner/replay |
| `parallel_replay` | replay service starts and serves samples |
