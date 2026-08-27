# Operator API: ops, Hub wrappers, and registration

This reference distills Towhee 1.1.3 operator runtime behavior for future agents. It covers operator invocation and development boundaries only; route training-loop design to [training-and-models](../../training-and-models/SKILL.md) and pipeline graph design to [pipeline-programming](../../pipeline-programming/SKILL.md).

## Public imports

| Need | Import | Notes |
|---|---|---|
| Operator wrappers | `from towhee import ops` or `from towhee.runtime import ops` | `ops` is an `Ops` object that creates lazy `_OperatorWrapper` instances. |
| Local registration | `from towhee import register` or `from towhee.runtime import register` | Alias for `OperatorRegistry.register`. |
| Base operator class | `from towhee.operator import Operator` | Abstract base with runtime key/device bookkeeping and `flush()`. |
| Pure Python operators | `from towhee.operator import PyOperator` | Intended for Python-only processing without ML framework training. |
| Neural-network operators | `from towhee.operator import NNOperator` | Intended for operators with framework-backed models; training requires a model. |

## How `ops` parses names

`ops` records chained attributes until the final call. The final call returns an `_OperatorWrapper`; the real operator loads lazily on the wrapper's first `__call__()` or `get_op()`.

| User expression | Wrapper name after normalization | What happens |
|---|---|---|
| `ops.my_namespace.my_operator('a', c='c')` | `my-namespace/my-operator` | Dots become `/`; underscores become `-`; init args/kwargs are stored. |
| `ops.add_operator(10)` | `add-operator` | Registry lookup is attempted first; if missing, Hub loading may fall back to `towhee/add-operator`. |
| `ops.local.add_operator(10)` | `local/add-operator` | Uses the local-operator path convention when a local cache is configured; this is distinct from `@register` unless names match. |
| `ops.image_decode.cv2('rgb')` | `image-decode/cv2` | Predeclared task families expose common Hub operators through the same wrapper machinery. |
| `ops.towhee.image_decode()` | `towhee/image-decode` | Explicit Hub namespace form. |

Wrapper state that is safe to inspect before loading:

| Property | Meaning |
|---|---|
| `name` | Normalized operator name. |
| `tag` | Selected revision tag, default `main`. |
| `init_args` / `init_kws` | Arguments captured for operator construction. |
| `is_latest` | Whether the call should refresh the cached Hub version. |

## Revision and latest behavior

- `wrapper.revision(tag='main')` mutates the same wrapper's `tag` and returns the wrapper.
- `wrapper.latest()` marks the same wrapper with `is_latest=True` and returns it.
- Cache behavior is revision-aware: a cached Hub operator is reused when the revision directory exists and `is_latest` is false.
- `.latest()` forces a Hub refresh for the selected tag and can overwrite that cached revision's symlinked version directory.
- For reproducible work, prefer `.revision('known-tag-or-branch')` and avoid `.latest()` unless the user explicitly wants fresh Hub content.
- A chain such as `ops.test_revision().revision('v1').latest()` keeps `tag == 'v1'` while requesting a refresh of that tag.

## Local registration with `register`

`register` accepts classes, functions, or callable objects.

### Class operator

```python
from towhee import ops, register
from towhee.operator import PyOperator

@register(name='scale_operator')
class ScaleOperator(PyOperator):
    def __init__(self, factor):
        self.factor = factor

    def __call__(self, value):
        return value * self.factor

op = ops.scale_operator(3)
assert op(4) == 12
```

### Function operator

```python
from towhee import ops, register

@register
def subtract(x, y):
    return x - y

op = ops.subtract()
assert op(7, 2) == 5
```

Registration facts:

| Fact | Consequence |
|---|---|
| `@register` without parentheses is supported. | The decorated function/class name is used. |
| `@register(name='foo_bar')` normalizes to an anonymous repo-style key like `anon/foo-bar`. | Call through `ops.foo_bar(...)` or another namespace-compatible expression; Python attributes use `_`, wrapper names use `-`. |
| A function is wrapped into a zero-argument callable class and also stored with a `_func` key. | Call `ops.func_name()` to construct the operator, then call the returned operator with data. |
| Registered callables without `shared_type` get `SharedType.Shareable`. | Explicit subclasses may override `shared_type`. |
| Registry lookup tries the raw name, `anon/<name>`, then `builtin/<name>`. | `ops.add_operator()` can resolve a registered anonymous operator even though the wrapper name lacks `anon/`. |

## Base-class boundaries

| Class | Use for | Public behavior and cautions |
|---|---|---|
| `Operator` | Custom operator base when you need runtime key/device bookkeeping. | Abstract `__init__` sets `_device_id` from runtime config or `-1`, initializes `_key`, exposes `key`, defaults `shared_type` to `NotShareable`, and provides no-op `flush()`. Implement `__call__`. |
| `PyOperator` | Python-only operators, preprocessing, postprocessing, light state. | Inherits `Operator`; `shared_type` is `NotShareable`. If overriding `__init__`, call `super().__init__()` when `key` or `_device_id` matters. |
| `NNOperator` | Model-backed operators involving ML frameworks. | Defaults `framework='pytorch'`, initializes `model`, `model_card`, and trainer state, and reports `SharedType.Shareable`. `train()` delegates to `setup_trainer()`. |

`NNOperator.setup_trainer()` imports PyTorch and requires `self.model` or `self._model` to be a `torch.nn.Module`. Without that model attribute, training raises `AttributeError('There is no trainable model attr in this operator.')`. Keep inference-only operators focused on `__call__`; use the training sub-skill for trainer configuration.

## Loader order and side effects

When an `_OperatorWrapper` loads, Towhee tries loaders in this order:

1. Internal runtime operators such as no-op helpers.
2. `OperatorRegistry` for locally registered functions/classes/callables.
3. Hub/cache loading. Names without `/` are treated as `towhee/<name>` for Hub fallback.

Hub/cache loading can install missing packages from an operator `requirements.txt` and can make network calls. Do not rely on Hub loading for fast offline validation; use registered tiny operators or help-only CLI checks instead.

## Native evidence distilled into this reference

- Installed public signature snapshot for Towhee 1.1.3.
- Operator wrapper tests for name normalization, captured constructor args/kwargs, revisions, latest refresh flags, local registry resolution, and lazy loading.
- User-pipeline tests for `@register`, `PyOperator`, `ops.local.*`, `ops.*`, `revision().latest()`, and `flush()` behavior.
- CLI and Hub cache behavior observed from the runtime loader and cache manager implementation.
