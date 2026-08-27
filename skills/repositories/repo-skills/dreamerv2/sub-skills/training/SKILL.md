---
name: training
description: "Run and troubleshoot DreamerV2 2.2.0 training through the native
  module runner or public Python API, including GPU-era runtime gates,
  replay/checkpoint/log lifecycle, bounded debug runs, and safe resume
  planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DreamerV2 training

Use this route when the task is to launch, bound, resume, or diagnose a
DreamerV2 training run. It covers the built-in `python -m dreamerv2.train`
workflow and `dreamerv2.api.train(env, config, outputs=None)`. It does not
replace the environment schema, full configuration catalog, or plotting
routes:

- Environment construction, wrappers, observation/action keys, and external
  suite assets: [environments](../environments/SKILL.md).
- Presets, typed flags, dotted overrides, and complete config values:
  [configuration](../configuration/SKILL.md).
- JSONL/TensorBoard inspection, plotting, and run comparison:
  [evaluation](../evaluation/SKILL.md).

## Choose the entry point

| Need | Entry point | Important boundary |
|---|---|---|
| DMC, Atari, or Crafter training | `python -m dreamerv2.train` | Requires a visible TensorFlow GPU and the selected suite/assets. |
| Custom Gym environment object | `dreamerv2.api.train(env, config, outputs=None)` | Uses the caller's legacy Gym environment; it has no native GPU assert. |
| Import/config/help check | `python -m dreamerv2.train --help` or a small Python process | Does not prove environment or training readiness. |
| Installed console command | Do not use `dreamerv2` for this release | Its launcher-relative `configs.yaml` lookup is broken. |

Read [workflows](references/workflows.md) before any run and
[troubleshooting](references/troubleshooting.md) when a run fails. Use a
writable, disposable `logdir`; the YAML placeholder `/dev/null` is not a run
location.

## Minimum safe procedure

1. Confirm the package/runtime pair before allocating a long run. The native
   runner is from the TensorFlow 2.6-era stack and uses legacy mixed-precision
   APIs; pin a coherent compatible environment rather than mixing modern
   TensorFlow Probability with old TensorFlow.
2. Validate the environment separately. For native tasks, use a valid
   `suite_task` such as `dmc_walker_walk`, `atari_pong`, or
   `crafter_reward`. For a custom environment, pass the raw legacy Gym object
   to the API and let its wrappers run; route the schema check to
   [environments](../environments/references/custom-gym.md).
3. Compose presets and overrides before training. Put `debug` last, set an
   explicit `--precision 32` when mixed precision is not verified, and use
   `--envs_parallel none` for the source snapshot's reliable serial path.
4. Create and test the log directory, then start with a bounded step target.
   Watch replay counts and the first checkpoint before increasing `steps`.
5. Stop on NaN/Inf losses, repeated empty-replay errors, OOM, or permission
   errors. Preserve `config.yaml`, `metrics.jsonl`, replay files, and
   `variables.pkl` for diagnosis; do not call a partial run successful.

## Native runner contract

```sh
python -m dreamerv2.train \
  --logdir "$RUN_DIR" \
  --configs atari debug \
  --task atari_pong \
  --steps 1200 \
  --precision 32 \
  --envs_parallel none
```

The runner loads `defaults`, applies `--configs` left to right, then parses
ordinary dotted flags. It creates the logdir and writes the effective
`config.yaml` before TensorFlow's GPU assertion. It then creates
`train_episodes/` and `eval_episodes/`, fills replay, constructs datasets and
an `Agent`, pretrains or loads it, alternates evaluation and collection, and
saves `variables.pkl` after each collection block. `steps` is the environment
counter; logged steps are multiplied by `action_repeat`.

The command above is a bounded shape of a native run, not a promise that Atari
ROMs or a GPU are installed. Do not run it until the native prerequisites pass.
The source snapshot also has a typo in the asynchronous branch that references
`eval_envs` while constructing evaluation workers. Keep `--envs_parallel none`
unless that branch has been patched and independently checked.

## Public API contract

```python
import dreamerv2.api as dv2

config = dv2.defaults.update({
    'logdir': 'runs/custom/1',
    'prefill': 12,
    'pretrain': 1,
    'replay.minlen': 5,
    'replay.maxlen': 5,
    'dataset.length': 5,
    'dataset.batch': 2,
    'steps': 15,
    'eval_every': 5,
    'train_every': 1,
    'log_every': 5,
    'time_limit': 5,
    'precision': 32,
})
dv2.train(env, config)  # returns None; persists run artifacts in logdir
```

`env` must be the raw legacy Gym object. The API applies
`GymWrapper -> ResizeImage -> OneHotAction` for discrete actions or
`NormalizeAction` for continuous actions -> `TimeLimit`. Do not pre-wrap it;
use the sibling environment skill for lifecycle keys and action bounds.
`outputs=None` installs terminal, JSONL, and TensorBoard outputs. A truthy
custom list must contain logger callables that accept the buffered metric list;
for example, a JSONL-only output can avoid video encoder dependencies.

The API path creates `config.yaml`, `train_episodes/`, metrics/events as they
are flushed, and `variables.pkl` after each `eval_every` collection block. It
has no evaluation environment or `eval_episodes/` directory, does not set the
TensorFlow GPU policy, and does not apply the CLI's `precision` or `jit` global
setup. A CPU API call may be useful for a carefully bounded compatibility
experiment, but it is not equivalent native-training verification.

## Lifecycle and resume rules

A replay episode is accepted only when its effective length is at least
`replay.minlen`; `eplen` is the number of actions minus one. The dataset also
needs a valid sequence of `dataset.length`. Prefill is a target based on
existing replay steps, not a guarantee that usable sequences exist. A short or
never-ending custom episode can therefore leave replay empty and fail at the
first `next(dataset)`.

`variables.pkl` contains pickled model/module variables, not replay, config, or
an authoritative step counter. The runner reconstructs the counter from
`train_episodes/*.npz` and loads the checkpoint only after a dataset batch has
built the variables. Resume only when the restored `config.yaml`, model shapes,
precision/runtime, and replay schema agree. If a checkpoint exists but replay
has too few valid sequences, lower compatible sequence thresholds only after
checking the saved config or collect enough new complete episodes by setting a
larger prefill target; never fabricate replay or treat a checkpoint-only copy
as a complete resume.

For exact artifact fields, command recipes, API details, and failure recovery,
open the three bundled references. Stop before a long run if any required
backend or external environment is unresolved.
