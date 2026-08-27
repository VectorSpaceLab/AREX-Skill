# Training API and artifact reference

## Public call signature

```python
dreamerv2.api.train(env, config, outputs=None)
```

- `env`: one raw legacy Gym environment object. It must expose
  `observation_space`, `action_space`, `reset()`, and the four-return
  `step(action)` contract. The API wraps it internally; see
  [custom Gym](../../environments/references/custom-gym.md) for observation,
  action, dtype, and truncation rules.
- `config`: a `dreamerv2.common.Config`, normally derived from
  `dreamerv2.api.defaults`. It must contain the complete agent, replay,
  dataset, logging, and cadence keys; do not pass an arbitrary dictionary.
- `outputs`: `None` selects terminal, JSONL, and TensorBoard outputs. A truthy
  iterable replaces all defaults. Each output is called with a list of
  `(step, name, numpy_value)` tuples. An empty list is falsy and therefore
  selects the defaults again.
- Return value: `None`. Progress is printed and state is persisted under
  `config.logdir`.

Use immutable config updates and parse only ordinary config flags:

```python
import dreamerv2.api as dv2

config = dv2.defaults.update({
    'logdir': 'runs/custom/1',
    'steps': 15,
    'prefill': 12,
    'replay.minlen': 5,
    'replay.maxlen': 5,
    'dataset.length': 5,
    'dataset.batch': 2,
}).parse_flags(['--precision', '32', '--jit', 'False'])
```

The API module also loads named YAML presets in `dv2.configs`. To reproduce
runner composition, update `dv2.defaults` with each selected preset in order,
then update explicit values. `--configs` is a runner-only flag and is not a
key in `dv2.defaults`; route full preset and typing questions to
[configuration](../../configuration/SKILL.md).

## API execution order

`api.train` performs the following operations synchronously:

1. Expand `config.logdir`, create it, and save the effective `config.yaml`.
2. Select default or caller-provided outputs and create a `Replay` at
   `logdir/train_episodes` using `config.replay`.
3. Create a `Counter` from replay `total_steps`, a `Logger` whose step
   multiplier is `config.action_repeat`, and cadence gates for training and
   logging.
4. Wrap the raw environment as
   `GymWrapper -> ResizeImage -> OneHotAction` for a discrete action or
   `NormalizeAction` for a continuous action -> `TimeLimit`.
5. Register driver callbacks: episode metrics/replay logging, step counting,
   replay insertion, and periodic agent updates/reports.
6. Prefill toward `config.prefill` steps with a random policy. Only completed
   episodes meeting `replay.minlen` become `.npz` files.
7. Build a replay dataset iterator, construct `agent.Agent`, call one training
   batch to create variables, then load `variables.pkl` if it exists or run
   `config.pretrain` batches.
8. Collect `config.eval_every` steps per outer block, train when
   `Every(config.train_every)` fires, log when `Every(config.log_every)` fires,
   and save `variables.pkl` after each block until `step >= config.steps`.

The API's `eval_every` name is inherited from the native configuration but is
collection-block length here; it does not run a separate evaluation
environment. The API has no `eval_replay` and never creates `eval_episodes/`.
It also does not configure TensorFlow GPU memory growth, eager/JIT mode, or
mixed precision from config. Set and validate those process-level choices
outside the call if an advanced API run truly needs them.

## Native runner differences

`python -m dreamerv2.train` additionally:

- loads `configs.yaml` relative to the module file and consumes `--configs`;
- asserts `tf.config.experimental.list_physical_devices('GPU')` is non-empty;
- sets memory growth for visible GPUs;
- sets eager execution from `jit` and, for `precision == 16`, imports the
  TensorFlow-era experimental mixed-precision policy;
- creates both `train_episodes/` and `eval_episodes/`;
- evaluates `eval_eps` episodes before each training collection block; and
- prefixes native episode/report metrics with `train_` or `eval_`.

Only `precision` values `16` and `32` pass the native assertion. The defaults
choose `16`; `debug` changes JIT/cadence and sequence values but does not
change precision. Use `--precision 32` for the first compatibility run.

## Persistent layout

Typical native layout:

```text
logdir/
  config.yaml
  metrics.jsonl
  events.out.tfevents.*
  variables.pkl
  train_episodes/*.npz
  eval_episodes/*.npz
```

Typical API layout omits `eval_episodes/`:

```text
logdir/
  config.yaml
  metrics.jsonl
  events.out.tfevents.*
  variables.pkl
  train_episodes/*.npz
```

Details:

- `config.yaml`: effective config written at startup, even if the native GPU
  assertion later fails. It is evidence of intent, not proof of a run.
- `train_episodes/`, `eval_episodes/`: compressed NumPy replay episodes. A
  filename's final length is the effective action count; short episodes are
  skipped by `Replay.add_episode`.
- `variables.pkl`: pickled module variables written after a collection block.
  It does not contain replay files, config, or the counter source.
- `metrics.jsonl`: append-only scalar rows written only when `Logger.write`
  has buffered metrics. API episode metrics are generally `return` and
  `length`; native metrics are generally `train_return`, `eval_return`, and
  prefixed replay/report values.
- TensorBoard event files: created lazily by `TensorBoardOutput`; video GIF
  encoding uses `ffmpeg` when present and otherwise falls back to an image
  summary. Missing events do not imply missing JSONL.

A logger step is `int(counter) * action_repeat`. Replay `total_steps` counts
effective episode actions and is the native resume counter. Use the evaluation
route for JSONL schemas, TensorBoard inspection, and plot layout.

## Replay and dataset invariants

`Replay(directory, capacity, ongoing, minlen, maxlen, prioritize_ends)` loads
valid `.npz` files at construction. It samples only completed episodes unless
`ongoing=True`; the training defaults use `ongoing=False`. The sampler requires
at least one episode and a valid `minlen`, and `dataset(batch, length)` uses
`drop_remainder=True`, so a batch cannot be formed from fewer than `batch`
samples.

For a reliable bounded run, ensure:

```text
episode effective length >= replay.minlen
episode effective length >= dataset.length
prefill produces at least one completed accepted episode
replay has enough samples for the requested batch
```

Prefer two or more complete episodes for a resume test. If all custom episodes
are shorter than `minlen`, the replay directory can exist while its in-memory
loaded episode set is empty; the first dataset sample then fails. Do not solve
this by touching `.npz` filenames; change the environment duration or a
compatible config and collect real transitions.

## Checkpoint compatibility

A load is attempted only after the first dataset batch has created variables.
Compare before resume:

- model dimensions and head/encoder key selection;
- action-space shape and discrete/continuous distribution;
- config precision/runtime and TensorFlow/TFP era;
- replay `minlen`/`maxlen`, dataset `length`/`batch`, and observation dtypes;
- action repeat and the replay directory used to reconstruct the counter.

Shape or nesting differences can raise an assignment error during
`Agent.load`; a config change can also make the restored variables semantically
invalid even if assignment happens to succeed. Keep the original directory
unchanged and test a copied resume directory. If replay is missing or too
short, restore it or deliberately collect enough new episodes before trusting
the checkpoint.
