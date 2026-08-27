---
name: "configuration"
description: "Routes DreamerV2 configuration construction, preset composition,
  typed flags, immutable updates, and schedule validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DreamerV2 configuration

Use this route to construct, inspect, serialize, or troubleshoot a DreamerV2
`common.Config` before handing it to training or the public API. The package
configuration is a typed, immutable flat/nested mapping; command-line flags
produce a new config rather than mutating the input.

## Route boundaries

Use this sub-skill for:

- the `defaults`, `atari`, `crafter`, `dmc_vision`, `dmc_proprio`, and `debug`
  YAML presets;
- ordered preset composition through `--configs`;
- dotted keys, regular-expression key updates, and typed flag values;
- `Config.update()`, `Config.save()`/`Config.load()`, and schedule syntax; and
- high-impact model, replay, dataset, precision, JIT, and training cadence
  choices that are configuration values.

Route elsewhere for:

- environment names, observation/action schemas, wrappers, or external assets:
  use `environments`;
- launching training, logdir/checkpoint/replay lifecycle, GPU setup, or resume:
  use `training`; and
- plot flags, metric aggregation, and run comparison: use `evaluation`.

Read the focused tables before changing a value:

- [references/presets.md](references/presets.md) — exact defaults, preset
  deltas, order, and high-impact choices.
- [references/flags-and-config.md](references/flags-and-config.md) — parser,
  conversion, immutability, patterns, persistence, and schedules.
- [references/troubleshooting.md](references/troubleshooting.md) — failure
  diagnosis and portable command recipes.
- [scripts/preview_config.py](scripts/preview_config.py) — safe, package-backed
  preset/override preview with no training side effects.

## Verified construction workflow

1. Start from the public package defaults. For the Python API, use
   `import dreamerv2.api as dv2` and `dv2.defaults`; for the built-in runner,
   provide a real writable `--logdir` rather than retaining `/dev/null`.
2. Select presets in the exact order they should override one another. The
   runner first parses `--configs`, starts from `defaults`, then calls
   `config.update(configs[name])` once for each selected name. Later presets
   win. `defaults` is the implicit selection when `--configs` is omitted.
3. Apply named dotted overrides after all presets, for example
   `--replay.minlen 10 --dataset.length 10 --precision 32`. Use the exact
   spelling and the value spelling documented in the references; do not invent
   flags.
4. Preview and validate with a small Python process before a costly run. The
   [safe preview helper](scripts/preview_config.py) is also available. The
   following is safe and does not create environments or checkpoints:

   ```sh
   python - <<'PY'
   import dreamerv2.api as dv2
   cfg = dv2.defaults.update({'logdir': '/tmp/dreamerv2-config-preview'})
   for name in ('atari', 'debug'):
     cfg = cfg.update(dv2.configs[name])
   cfg = cfg.parse_flags(['--replay.minlen', '10', '--replay.maxlen', '30'])
   print(cfg)
   print('flat replay:', {k: v for k, v in cfg.flat.items()
                          if k.startswith('replay.')})
   PY
   ```

   `--configs` is a runner flag; it is not a key in `dv2.defaults`. For direct
   Python composition, load the package's preset mapping or reproduce the
   runner's ordered `Config.update()` calls, then call `parse_flags()` only for
   ordinary config keys.
5. Save a validated configuration beside a run with `config.save(path)`, or
   load a prior `.yaml`, `.yml`, or `.json` using `Config.load(path)`. The
   training runner saves its effective config as `config.yaml` in `logdir`.
6. Hand the resulting config to `dv2.train()` or to the `training` route. This
   sub-skill does not launch training. The installed console launcher is known
   to resolve `configs.yaml` from `sys.argv[0]`; use the verified module route
   `python -m dreamerv2.train ...` instead.

## Fast checks

- `python -m dreamerv2.train --help` is a help-only parser check; it does not
  prove that a selected environment or GPU can train.
- A typed config check should assert that YAML lists become tuples, a fractional
  integer is rejected, and a typo is rejected by `Config.update()`.
- A schedule check should evaluate one value at step 0, one interior value, and
  the endpoint using TensorFlow tensors. See the exact formulas in
  [references/flags-and-config.md](references/flags-and-config.md).
- Keep generated `config.yaml` portable: use a path valid on the target host,
  avoid source-checkout paths, and record the effective config after preset and
  flag composition. Precision/JIT and environment availability still belong to
  the downstream training gate.

## High-impact decisions

- Choose `dmc_vision` versus `dmc_proprio` according to the observation modality;
  their encoder/decoder key filters and preset model sizes differ.
- `atari` changes image keys, action repeat, time limit, horizon, replay
  prefill, optimizer rates, entropy, discount, and loss scales. It is not just
  a task-name alias.
- `crafter` enables image-only model keys, achievement/reward logging, and a
  regex update that sets every existing `*.norm` key to `layer`.
- `debug` must normally be last. It disables JIT and shortens evaluation,
  logging, prefill, replay, and dataset settings; it does not make the native
  runner CPU-safe, nor does it override `precision`.
- `precision` accepts only 16 or 32 in the built-in runner. `jit: False` enables
  eager TensorFlow functions; `jit: True` leaves graph compilation enabled.
  These are runtime choices, not proof that a config is otherwise valid.

If a flag fails, preserve the exact error and compare it with
[references/troubleshooting.md](references/troubleshooting.md); do not silently
coerce a typo, fractional integer, empty list, or non-canonical boolean.
