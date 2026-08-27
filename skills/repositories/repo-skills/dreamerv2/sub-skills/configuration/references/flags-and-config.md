# Flags, immutable configs, persistence, and schedules

This reference records the behavior implemented by `dreamerv2.common.config`,
`dreamerv2.common.flags`, and `dreamerv2.common.other.schedule` in the inspected
snapshot. Examples use the installed package modules and do not depend on a
source checkout.

## Config representation

```python
from dreamerv2 import api
Config = api.Config

cfg = Config({'model': {'lr': 1e-4}, 'names': ['image'], 'enabled': True})
assert cfg['model.lr'] == cfg.model.lr == 1e-4
assert cfg.names == ('image',)
```

Construction first flattens nested dictionaries into dotted keys, validates
keys, JSON-round-trips values, converts lists to tuples, and rebuilds a nested
mapping. `cfg.flat` returns a copy of the flat mapping. Nested access accepts a
dotted string (`cfg['model.lr']`) or an attribute (`cfg.model.lr`); asking for a
mapping such as `cfg['model']` returns another `Config`.

Keys may contain only letters, digits, underscore, dot, and hyphen. A key with
any other character is treated as a regex pattern by update/flag operations,
but direct `Config(...)` construction rejects it with an assertion. This is
why pattern updates are supplied to `update()` rather than placed in a base
config.

### Immutable update

Assignment through normal config syntax is rejected:

```python
cfg['model.lr'] = 2e-4  # AttributeError: immutable config; use update()
cfg.model.lr = 2e-4    # AttributeError
cfg2 = cfg.update({'model.lr': 2e-4})
```

`update()` copies the flat mapping and returns a new `Config`; the original is
unchanged. It flattens nested input, then processes each input entry in input
iteration order. For a literal key, the key must already exist. The new value
is converted with `type(old)(new)`, with one explicit guard: an integer old
value may not receive a fractional float. This preserves common scalar types
and rejects conversion errors as a `TypeError` naming the key, old value, and
expected type.

A pattern key is any key matching the class regex
`.*[^A-Za-z0-9_.-].*`. It is compiled and matched with `pattern.match()` against
every existing flat key. All matching keys are updated; matching is not
search-anywhere and patterns do not create keys. A pattern with no matches
raises `KeyError("Unknown key or pattern ...")`. Because `update()` processes
entries in sequence, later entries can overwrite values changed by an earlier
pattern. A regex update can intentionally update several model normalization
leaves at once:

```python
layered = cfg.update({r'.*\.norm': 'layer'})
```

The pattern is not a persistent key in `layered.flat`; only matched concrete
keys remain. Escape the dot when you mean a literal dotted separator. A broad
pattern such as `.*norm` can change more keys than expected, so inspect
`cfg.flat` and the returned config.

### Values and type limits

| Input/default form | Construction result | Flag value syntax |
|---|---|---|
| `True` / `False` | Python bool | exactly `True` or `False`; spelling is case-sensitive |
| integer | Python int | decimal or scientific notation, but no fractional result |
| float | Python float | any value accepted by `float()` |
| string | Python str | one string token |
| `None` | `None` | any one token becomes a string |
| non-empty homogeneous list | tuple | repeated tokens or one comma-separated token |
| non-empty homogeneous tuple | tuple | repeated tokens or one comma-separated token |

Construction rejects an empty list/tuple because its element type cannot be
inferred. It also rejects a list whose elements are not all the same type, or
whose first element is not a string, float, int, or bool. JSON-compatible
nested values are required by the construction round trip. A tuple's element
type is inferred from its first element; flag parsing converts every selected
element using that first element's type.

The integer conversion details are important:

- `--steps 1e6` is accepted because flags parse integer defaults through
  `float()` and then `int()`.
- `--steps 1.5` is rejected with `TypeError` before config update.
- A direct `cfg.update({'steps': 1.5})` is rejected by the explicit fractional
  guard; `cfg.update({'steps': '100'})` converts the string to `100`.
- Numeric YAML such as `1e8` may be loaded as a float, so check `cfg.flat[key]`
  rather than assuming a visual YAML spelling determines the Python type.

Boolean flags do not use Python truthiness. They evaluate the exact token by
looking it up in `['False', 'True']`; `--jit false`, `--jit 0`, and
`--jit FALSE` all fail with `Expected bool ...`. Use `--jit False` or
`--jit True`.

## Flags parser

`Config.parse_flags(argv=None, known_only=False, help_exists=None)` creates a
`Flags` parser around the config. If `argv` is omitted, it reads `sys.argv[1:]`.
Each `--key` starts an entry and subsequent non-flag tokens belong to it until
the next `--key`; `--key=value` is also accepted. A value token before any
flag is collected as positional remainder and is rejected by normal parsing.

Examples:

```python
parsed = cfg.parse_flags([
    '--jit', 'False', '--replay.minlen', '10',
    '--render_size', '84', '84', '--log_keys_video', 'image,log_image'])
```

For scalar config values exactly one token is required. For tuple/list values,
multiple tokens are accepted; one token containing a comma is split on commas.
No whitespace trimming is performed after splitting, so do not write spaces
around comma-separated values. The result is a new config.

A key containing regex metacharacters is treated as a regex and applies to all
matching existing flat keys. For example, `--.*\.norm layer` changes all
matching normalization leaves. Dotted ordinary keys such as `--model_opt.lr`
are literal config keys, not regexes, because dot is in the ordinary-key
character set. A flag that does not match a key is held in `remaining` during
parsing. With `known_only=False` (the default), an unmatched `--flag` finally
raises `ValueError("Flag '--flag' did not match any config keys.")`; with
`known_only=True`, the caller receives `(new_config, remaining)` so a separate
parser can consume a controlled flag such as `--configs`.

Other exact parser errors:

| Situation | Result |
|---|---|
| `--key` without values | `ValueError`, flag was not followed by values |
| bare values before a flag | `ValueError`, values were not preceded by a flag |
| scalar with two values | assertion from scalar parser |
| invalid bool | `TypeError`, expected bool |
| fractional integer | `TypeError`, expected int but got float |
| `--help` | prints a generated flat-key help listing; exits when `help_exists` is true |

`known_only` does not validate or discard unknown positional tokens. It is a
routing mode used by `train.py`; do not use it as a general typo suppressor.
When parsing `--help`, the default `help_exists` is `not known_only`: normal
parsing exits after printing help, while known-only parsing can retain control
of the caller when `help_exists=False`.

### `--configs` and preset flags

The built-in runner uses `common.Flags(configs=['defaults']).parse(known_only=True)`
to consume the `--configs` tuple. It then applies those named YAML blocks to a
fresh defaults config and parses the remaining ordinary keys. Therefore:

```sh
python -m dreamerv2.train --configs atari debug \
  --replay.minlen 10 --replay.maxlen 30 --precision 32
```

means presets in `defaults → atari → debug` order, then the three final
ordinary overrides. `--configs=atari` is equivalent to a one-value config
selection. A positional value such as `--configs atari debug` belongs to the
same flag until the next `--`; a later unknown `--something` is returned by the
known-only parse and then fails during the ordinary parse.

## Save and load

```python
from dreamerv2 import api
Config = api.Config
cfg = api.defaults.update({'logdir': '/tmp/dv2'})
cfg.save('/tmp/dv2-config.yaml')
cfg.save('/tmp/dv2-config.json')
restored_yaml = Config.load('/tmp/dv2-config.yaml')
restored_json = Config.load('/tmp/dv2-config.json')
```

`.yaml` and `.yml` use `ruamel.yaml.safe_dump`/`safe_load`; `.json` uses the
standard library JSON functions. Any other suffix raises `NotImplementedError`.
The saved document is the nested effective config; tuple values serialize as
YAML/JSON sequences and load back through `Config`'s list-to-tuple normalization.
Use explicit extensions and ensure the destination parent exists. The
training runner writes `logdir/config.yaml` after parsing and before the GPU
assertion, so a failed native launch may still leave an effective config if the
logdir was writable.

A saved config is not a checkpoint and does not encode installed package
versions, external environment assets, GPU availability, or source provenance.
Treat it as a portable parameter snapshot: use a target-host path, avoid
private checkout paths, and revalidate environment-dependent settings.

## Schedule syntax

`common.schedule(string, step)` first tries `float(string)`. Numeric strings are
constant schedules. Otherwise it checks the four `re.match()` patterns below;
use the canonical form with no spaces or extra arguments because the patterns
are not a general expression parser. `step` is cast to `tf.float32`; the result
is a TensorFlow scalar when a tensor or numeric step reaches the arithmetic.

| Form | Formula | Endpoint behavior |
|---|---|---|
| `linear(initial,final,duration)` | `(1-mix)*initial + mix*final`, `mix=clip(step/duration,0,1)` | starts `initial`, reaches `final` at `duration`, stays there |
| `warmup(warmup,value)` | `clip(step/warmup,0,1)*value` | starts 0, reaches `value` at `warmup`, stays there |
| `exp(initial,final,halflife)` | `(initial-final)*0.5**(step/halflife)+final` | starts `initial`; approaches `final` asymptotically |
| `horizon(initial,final,duration)` | `1 - 1 / ((1-mix)*initial + mix*final)` with clipped `mix` | interpolates the horizon, then returns its reciprocal complement |

Examples:

```python
from dreamerv2 import api
import common  # available after importing dreamerv2.api in this package
schedule = common.schedule
schedule('0.1', 0)                 # Python float 0.1
schedule('linear(1,0,100)', 50)    # TensorFlow scalar ~0.5
schedule('warmup(100,0.2)', 50)     # ~0.1
schedule('exp(1,0.25,10)', 10)      # 0.625
schedule('horizon(1,10,100)', 100)  # 0.9
```

The implementation does not validate zero or negative durations/halflives.
Those values can produce division-by-zero or mathematically unsuitable
schedules; choose positive values. Malformed text raises `NotImplementedError`.
The agent calls this helper for `actor_grad_mix` and `actor_ent`. In the
shipped defaults those leaves are floats, so ordinary typed flag parsing expects
a float rather than a schedule expression. The helper itself also accepts a
schedule string when called directly; other string config leaves remain strings
unless their consumer explicitly calls `schedule()`.
