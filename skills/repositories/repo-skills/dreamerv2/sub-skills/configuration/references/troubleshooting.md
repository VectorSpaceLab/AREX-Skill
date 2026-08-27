# Configuration troubleshooting

Start by reproducing configuration construction without launching an
environment. Keep the exact command, selected preset order, and final flat
values. Then route runtime failures to `training` or `environments` when the
config itself is valid.

## Safe preview and assertion check

The skill-owned helper gives a package-backed preview without creating a
logdir, environment, replay, checkpoint, or TensorBoard writer:

```sh
python skills/disco/dreamerv2/sub-skills/configuration/scripts/preview_config.py \
  --configs atari debug \
  --set replay.minlen=10 \
  --set replay.maxlen=30 \
  --set precision=32
```

Its `--configs` and repeated `--set key=value` options are helper syntax. The
actual runner syntax remains `python -m dreamerv2.train --configs ...
--key value`; the helper converts each `--set` entry into the package's own
`Config.parse_flags()` behavior. It prints the effective config and selected
flat values, and exits nonzero on an unknown key, invalid type, or unknown
preset.

A minimal direct check is:

```sh
python - <<'PY'
from dreamerv2 import api
cfg = api.defaults
for name in ('atari', 'debug'):
  cfg = cfg.update(api.configs[name])
cfg = cfg.parse_flags(['--replay.minlen', '10', '--precision', '32'])
assert cfg.replay.minlen == 10 and isinstance(cfg.replay.minlen, int)
assert cfg.replay.maxlen == 30
assert cfg.precision == 32
try:
  cfg.update({'replay.minln': 10})
except KeyError:
  pass
else:
  raise AssertionError('typos must not create config keys')
try:
  cfg.parse_flags(['--jit', 'false'])
except TypeError:
  pass
else:
  raise AssertionError('booleans are case-sensitive')
PY
```

## Unknown key or pattern

**Symptoms:** `KeyError: Unknown key or pattern ...` from `Config.update()`,
or `ValueError: Flag '--...' did not match any config keys.` from final flag
parsing.

**Diagnosis:** flatten the effective config and compare the requested spelling:

```python
print(sorted(cfg.flat))
```

`replay.minlen` is an existing literal key. `replay.minln` is not. A literal
key may contain letters, digits, `_`, `.`, or `-`; a typo that introduces regex
metacharacters can instead be interpreted as a pattern. A pattern that matches
nothing is still an error. `known_only=True` delays an unknown flag for the
caller; it does not make it valid.

**Fix:** correct the key, or deliberately use a pattern that matches at least
one current flat key. Do not add a new key through `update()`; this API is for
updating the established config schema.

## Regex update changed multiple keys

A pattern update is intentionally broadcast. For example, after defaults are
loaded:

```python
before = {k: v for k, v in cfg.flat.items() if k.endswith('.norm')}
cfg2 = cfg.update({r'.*\.norm': 'layer'})
after = {k: v for k, v in cfg2.flat.items() if k.endswith('.norm')}
print(before)
print(after)
```

All current keys matching `re.match(r'.*\.norm', key)` change, including
`rssm.norm`, `encoder.norm`, `decoder.norm`, `reward_head.norm`,
`discount_head.norm`, `actor.norm`, `critic.norm`, and `expl_head.norm` in the
base schema. The update does not change `reward_norm.momentum`,
`expl_reward_norm.scale`, or any key that merely contains `norm` elsewhere.
The Crafter preset deliberately uses this same mechanism. Inspect matches
before applying a broad command-line pattern:

```sh
python skills/disco/dreamerv2/sub-skills/configuration/scripts/preview_config.py \
  --set '.*\.norm=layer'
```

Quote regex flags in a shell command so globbing and backslash processing do
not alter them. A pattern uses `re.match`, so anchor or shape it to match from
the beginning; `.*` is useful when matching a suffix. Patterns apply only to
keys present at the time of the update and never create a new key.

## Wrong boolean spelling

**Symptom:** `TypeError: Expected bool but got 'false' for key 'jit'.`

Use capitalized tokens exactly:

```sh
python -m dreamerv2.train --configs debug --jit False
python -m dreamerv2.train --configs debug --atari_grayscale True
```

`False`, `True`, `false`, `true`, `0`, and `1` are not interchangeable in the
flag parser. A direct `Config.update()` is different: it invokes `bool(new)`
for a bool old value, so a non-empty string such as `'False'` becomes `True`.
Pass a real Python bool in direct updates; use `parse_flags()` for CLI text.

## Integer fractional conversion

**Symptom:** `--imag_horizon 15.5` fails with an expected-int error.

The flag parser accepts scientific notation for integer defaults by converting
the token through `float()`, but requires an integral result. Thus
`--imag_horizon 1e1` is accepted as `10`, while `--imag_horizon 15.5` is
rejected. Direct `Config.update()` also rejects a fractional float for an
integer old value. Inspect the loaded type first because YAML values such as
`1e8` can be floats and then follow float conversion rules.

## Preset override order

**Symptom:** a value appears to ignore `debug`, or a DMC/Atari value reappears.

Print the value after each update:

```python
from dreamerv2 import api
cfg = api.defaults
for name in ('atari', 'debug'):
  cfg = cfg.update(api.configs[name])
  print(name, cfg.jit, cfg.replay.minlen, cfg.dataset.length,
        cfg.action_repeat, cfg.task)
```

The runner always starts from defaults, applies `--configs` left-to-right, then
ordinary flags. Use `--configs atari debug` when debug should shorten Atari;
use `--configs debug atari` only when Atari should win overlapping values.
Nested updates preserve omitted siblings: `debug` changes replay `minlen` and
`maxlen`, not capacity, ongoing, or prioritize-ends. A final
`--replay.minlen 10` wins over every preset.

## Empty list or type ambiguity

**Symptom:** config construction raises that empty lists are disallowed, or a
list flag fails to convert.

`Config` cannot infer the element type of `[]` and rejects empty lists/tuples.
For a non-empty tuple default, pass repeated values or one comma-separated
value:

```sh
python -m dreamerv2.train --render_size 84 84
python -m dreamerv2.train --render_size 84,84
python -m dreamerv2.train --configs atari --grad_heads decoder reward
```

Do not insert spaces around commas. The parser uses the first tuple element's
type for every element and returns a tuple. A heterogeneous list is rejected at
construction; a tuple update with incompatible values fails type conversion.

## Malformed schedule

**Symptoms:** `NotImplementedError` from `common.schedule`, NaN/Inf values, or
an unexpected schedule type.

Valid forms are `linear(initial,final,duration)`, `warmup(warmup,value)`,
`exp(initial,final,halflife)`, and `horizon(initial,final,duration)`, with each
numeric group accepted by `float()`. A plain numeric string is constant. Check
all commas, parentheses, and numeric groups. The implementation uses
`re.match()` rather than a full-string validator, so do not rely on suffixes or
other accidental matches; supply the canonical form. Durations and halflives
must be positive for meaningful results; the helper does not guard division by
zero.

The runner's defaults for `actor_ent` and `actor_grad_mix` are floats. Passing a
schedule expression to those ordinary CLI flags attempts `float(expression)`
and fails. A schedule expression is usable only if the final config leaf is a
string (for example, construct a custom `Config` with that leaf as a string)
and the consumer calls `common.schedule()`. Do not document a schedule as a
magic generic flag type.

## `config.yaml` portability

**Symptoms:** load fails on another machine, output directory is missing, or a
saved config does not reproduce the intended run.

- Save only after constructing the effective config; presets and command-line
  overrides are not recorded separately.
- Use `.yaml`, `.yml`, or `.json`; other suffixes are unsupported.
- `Config.save()` does not create parent directories. The runner creates its
  logdir before saving; standalone scripts must create the parent first.
- Use a writable target-host `logdir`. `/dev/null` is the YAML placeholder, not
  a directory. `~` is expanded by training when it constructs the path, but
  the saved value is still the config string.
- A saved file is a parameter snapshot, not a checkpoint or package lock. It
  does not record TensorFlow/TensorFlow Probability versions, external Atari,
  DMC, Crafter, or Gym assets, GPU capability, or source commit.
- YAML/JSON sequences load as tuples through `Config`; numeric representation
  in the file determines the loaded Python scalar type. Recheck integer and
  float assumptions after loading.

## Precision and JIT mismatch

**Symptoms:** debug run still needs a GPU, mixed-precision behavior differs,
or an apparently valid config fails at startup.

The built-in `train.py` asserts at least one TensorFlow GPU before training,
even with `debug` and `jit: False`. The runner then accepts only
`precision in (16, 32)`; precision 16 installs the TensorFlow experimental
mixed-precision policy, while 32 leaves it disabled. `jit: False` calls
`tf.config.experimental_run_functions_eagerly(True)` and `jit: True` leaves
compiled execution enabled. Neither setting validates environment suites,
external assets, or model/observation compatibility.

For numerical instability or infinite gradient norms, try a controlled
`--precision 32` configuration as the README suggests, but keep the native GPU
requirement and route the actual run to `training`. For missing observations,
wrong action spaces, or suite assets, use `environments` instead.

## Broken launcher and help checks

Use the module route for package help and configuration parsing:

```sh
python -m dreamerv2.train --help
```

This is a parser/help check, not a training smoke test. The installed console
entry point may fail before parsing because of its `sys.argv[0]`-relative
`configs.yaml` lookup. Do not repair that launcher from this sub-skill; use the
verified module route and route launch/checkpoint concerns to `training`.
