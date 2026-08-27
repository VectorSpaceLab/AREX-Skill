# Training workflows

## 1. Preflight and bounded-run policy

Treat training as a write-heavy, GPU-bound operation. Before a run:

```sh
python - <<'PY'
import pathlib
import tensorflow as tf
import dreamerv2
import dreamerv2.api as api
print('dreamerv2 import:', dreamerv2)
print('api.train:', api.train)
print('TensorFlow:', tf.__version__)
print('GPUs:', tf.config.experimental.list_physical_devices('GPU'))
PY
```

For the native module route, a non-empty GPU list is a hard gate. A successful
import or `--help` is not a training smoke test. Confirm external suite assets
separately; the native runner can only construct DMC, Atari, and Crafter from a
`suite_task`. Use the [environment route](../../environments/SKILL.md) for
schemas, wrappers, ROMs, MuJoCo, render libraries, and custom Gym handoff.

Select a new writable directory and test it before starting:

```sh
RUN_DIR="$(pwd)/runs/atari_pong/dreamerv2/1"
mkdir -p "$RUN_DIR"
test -w "$RUN_DIR"
python - <<'PY' "$RUN_DIR"
import pathlib, sys
p = pathlib.Path(sys.argv[1])
probe = p / '.write-probe'
probe.write_text('ok')
probe.unlink()
print('writable:', p)
PY
```

Do not use the default `/dev/null` logdir. Do not start with benchmark-scale
`steps`; use a bounded target, inspect the first replay files and checkpoint,
and then deliberately extend the run. Keep one run per logdir. A second
process writing the same JSONL, replay, or checkpoint files can corrupt the
resume state.

## 2. Built-in module workflow

The supported installed-package invocation is:

```sh
python -m dreamerv2.train \
  --logdir "$RUN_DIR" \
  --configs atari debug \
  --task atari_pong \
  --steps 1200 \
  --precision 32 \
  --envs_parallel none
```

Use `dmc_vision`, `dmc_proprio`, or `crafter` instead of `atari` when the
selected environment requires it. `--configs` is ordered: `defaults` is the
base, each named preset is applied left to right, and ordinary flags override
those presets. `debug` reduces cadence and sequence sizes but is not a CPU
mode; it leaves the default `precision: 16`, so explicitly pass `--precision
32` when validating an unverified mixed-precision path. Full preset and flag
semantics belong to [configuration](../../configuration/SKILL.md).

The source runner performs this lifecycle:

1. Resolve package `configs.yaml`, parse `--configs`, compose the effective
   config, parse remaining flags, create `logdir`, and save `config.yaml`.
2. Import TensorFlow, set eager execution according to `jit`, assert at least
   one physical GPU, enable GPU memory growth, and install the legacy
   `mixed_float16` policy when `precision == 16`. Only `16` and `32` pass.
3. Create `train_episodes/` and `eval_episodes/` replay stores. The training
   replay uses `config.replay`; evaluation replay uses capacity/length derived
   from the config. The counter starts at replay's `total_steps`.
4. Attach terminal, JSONL, and TensorBoard logger outputs. The JSONL file is
   append-only and may not exist until the first scalar flush.
5. Construct native environments, prefill train replay and one eval episode,
   build train/report/eval datasets, create the `Agent`, and run one initial
   train call to create variables. Load `variables.pkl` if present; otherwise
   run `pretrain` updates.
6. For each outer block, report/evaluate for `eval_eps` episodes, collect
   `eval_every` training steps, train every `train_every` step for
   `train_steps`, log at `log_every`, and save `variables.pkl`.
7. Close environments at normal completion. A killed process may leave a
   valid checkpoint but an incomplete final JSONL line; inspect it before
   resuming.

For a help-only parser check, use:

```sh
python -m dreamerv2.train --help
```

This should print config flags without creating environments or starting a
run. The installed `dreamerv2` console script is not the supported equivalent:
`train.py` derives `configs.yaml` from `sys.argv[0]`, so an installed launcher
looks beside its bin script rather than beside the package data. Use the module
command even when the distribution was installed from a wheel.

The native async option is not part of the safe baseline for this snapshot.
The `envs_parallel != none` branch contains a source typo using `eval_envs` as
an iterable before it has been defined. Keep serial workers unless a local
patch has been tested and is recorded with the run.

## 3. Bounded custom-Gym API run

The API accepts an environment object, not a task name. A tiny legacy Gym
fixture should have episodes at least as long as `replay.minlen` and should
terminate or truncate predictably. The following is an exact bounded pattern;
replace only `TinyEnv` with a caller-owned legacy Gym environment:

```sh
python - <<'PY'
import pathlib
import gym
import numpy as np
import dreamerv2.api as dv2

class TinyEnv(gym.Env):
  def __init__(self):
    self.observation_space = gym.spaces.Box(-1, 1, (4,), dtype=np.float32)
    self.action_space = gym.spaces.Discrete(2)
    self.t = 0
  def reset(self):
    self.t = 0
    return np.zeros(4, np.float32)
  def step(self, action):
    assert self.action_space.contains(action)
    self.t += 1
    done = self.t >= 5
    return np.zeros(4, np.float32), 1.0, done, {'is_terminal': False}

run = pathlib.Path('runs/custom/tiny/1')
config = dv2.defaults.update({
    'logdir': str(run), 'steps': 15, 'prefill': 12, 'pretrain': 1,
    'eval_every': 5, 'train_every': 1, 'train_steps': 1, 'log_every': 5,
    'time_limit': 5, 'replay.minlen': 5, 'replay.maxlen': 5,
    'dataset.length': 5, 'dataset.batch': 2, 'precision': 32,
    'encoder.cnn_keys': '$^', 'decoder.cnn_keys': '$^',
    'rssm.hidden': 32, 'rssm.deter': 32, 'rssm.stoch': 4,
    'rssm.discrete': 4, 'encoder.mlp_layers': [32],
    'decoder.mlp_layers': [32], 'actor.layers': 1, 'actor.units': 32,
    'critic.layers': 1, 'critic.units': 32, 'reward_head.layers': 1,
    'reward_head.units': 32, 'discount_head.layers': 1,
    'discount_head.units': 32, 'imag_horizon': 3,
})
dv2.train(TinyEnv(), config, outputs=[dv2.JSONLOutput(run)])
assert (run / 'config.yaml').is_file()
assert (run / 'variables.pkl').is_file()
assert list((run / 'train_episodes').glob('*.npz'))
print('bounded API run complete:', run)
PY
```

This deliberately uses a JSONL-only output, so missing `ffmpeg` or TensorBoard
is not a blocker for the scalar lifecycle check. Under a compatible runtime,
validate that `config.yaml`, at least one accepted replay `.npz`, `metrics.jsonl`,
and `variables.pkl` exist. The API returns `None`; artifacts and printed
metrics are the observable result. The example's `precision` value documents
intent but does not install a mixed-precision policy in `api.train`.

Do not pre-apply `GymWrapper`, `ResizeImage`, `OneHotAction`, or
`NormalizeAction` to the raw environment before this call. For modern
five-return Gym/Gymnasium environments, use the legacy compatibility shim and
verify its terminal/truncation semantics in the environment route before
training.

## 4. Resume planning

A valid resume is a matched set, not just a `variables.pkl` file:

```text
logdir/
  config.yaml
  variables.pkl
  train_episodes/*.npz
  metrics.jsonl                 # useful evidence, not required to load
```

Before resuming, compare the effective config with `config.yaml`, especially
model dimensions, observation key filters, action shape, replay min/max
length, dataset length/batch, precision, and action repeat. Count accepted
replay steps and verify that at least one episode can produce a dataset chunk.
The runner's counter comes from replay filenames, while the checkpoint stores
only module variables. A checkpoint can therefore load with a stale or empty
replay directory and still fail before the load at `next(train_dataset)`.

If replay is too short, first restore the original replay directory. If that is
impossible, use a compatible config with a smaller sequence threshold and a
prefill target greater than the current replay step count, then verify new
complete episodes before relying on the checkpoint. If the saved architecture
or environment schema cannot be matched, start a new logdir rather than
forcing assignment into `variables.pkl`. Never overwrite a valuable run while
experimenting with a repair; copy it to a new resume directory.

## 5. Artifact checklist

At the first safe stop, record:

- effective `config.yaml`, selected presets, overrides, package/runtime versions;
- GPU visibility and external environment readiness;
- counts and lengths under `train_episodes/` and, for native runs,
  `eval_episodes/`;
- last valid JSONL row and whether TensorBoard event files exist;
- checkpoint timestamp/size and whether it was saved after a completed block;
- exact `steps`, `action_repeat`, `prefill`, `train_every`, `train_steps`,
  `eval_every`, `replay.minlen`, and `dataset.length` values.

Route metric reading and plotting to [evaluation](../../evaluation/SKILL.md).
Do not infer successful evaluation from the presence of `variables.pkl`, and do
not treat replay directories as plot input.
