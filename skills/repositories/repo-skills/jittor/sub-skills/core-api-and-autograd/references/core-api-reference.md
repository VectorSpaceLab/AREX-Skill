# Core API Reference

Use this reference for `Var` creation, root tensor ops, broadcasting, `Module` and `Function` conventions, shape/dtype rules, and local serialization.

## Verified root signatures

| API | Verified signature | Notes |
| --- | --- | --- |
| `jt.array` | `(data, dtype=None)` | Builds a `Var` from Python scalars, lists, NumPy arrays, or another `Var`. |
| `jt.zeros` | `(*shape, dtype='float32')` | Constant zeros; shape may be passed as variadic ints or a tuple/list. |
| `jt.ones` | `(*shape, dtype='float32')` | Constant ones; same shape rules as `zeros`. |
| `jt.rand` | `(*size, dtype='float32', requires_grad=True)` | Uniform random values in `[0, 1)`. In the verified package, dtype arguments other than `float32` did not change the returned dtype. |
| `jt.random` | `(shape, dtype='float32', type='uniform')` | Random tensor; `type` is `uniform` or `normal`. In the verified package, dtype arguments other than `float32` did not change the returned dtype. |
| `jt.grad` | `(loss, targets, retain_graph=True)` | Backpropagates from `loss` to one `Var` or a list of `Var`s. |
| `jt.flag_scope` | `(**jt_flags)` | Temporary flag override context manager. |
| `jt.no_grad` | `(**jt_flags)` | Shortcut scope that sets `no_grad=1`. |
| `jt.enable_grad` | `(**jt_flags)` | Shortcut scope that sets `no_grad=0`. |
| `jt.save` | `(params_dict, path: str)` | Saves a Python container of Vars / arrays / scalars to a local file. |
| `jt.load` | `(path: str)` | Loads a local file or a URL-like checkpoint path. |
| `jt.sync_all` | `void sync_all(bool device_sync=false)` | Flushes all pending work; `True` also device-synchronizes. |
| `jt.set_seed` | builtin seed setter | Seeds Jittor's RNG for reproducible random tensors when used with immediate sync. |
| `jt.misc.set_global_seed` | `(seed, different_seed_for_mpi=True)` | Seeds Python, NumPy, and Jittor together. |

## Var essentials

- `Var` is the basic value type. Printing a Var shows shape and dtype; `np.array(var)` works because `Var.__array__ = Var.numpy`.
- `Var.data` is a synchronization boundary. Accessing it forces the queued work to finish and returns host-visible data.
- `Var.numpy()` is the NumPy conversion path; use it when you want an explicit host array.
- `Var.name("tag")` stores a debug name and `Var.name()` reads it back.
- `Var.requires_grad` toggles gradient tracking on the live Var.
- `Var.stop_grad()` and `Var.start_grad()` switch whether future gradients flow through that Var.
- `Var.sync()` waits on a single Var; `jt.sync_all()` waits on all pending work.
- `Var.peek()` is a compact debug string such as `float32[3,]`.

### Example

```python
import jittor as jt
import numpy as np

x = jt.array([1, 2, 3])
y = jt.ones(3, dtype='float32')
z = x + y

assert tuple(z.shape) == (3,)
assert str(z.dtype) == 'float32'
assert np.allclose(z.data, [2, 3, 4])
```

## Shape and dtype rules

- `jt.array(1)` produces a length-1 Var, not a scalar NumPy 0-d array.
- `jt.ones` and `jt.zeros` honor explicit dtype requests in the verified package.
- `jt.rand` and `jt.random` default to `float32`; in the verified package they also returned `float32` when `float64` or `int32` was requested, so cast explicitly when random dtype fidelity matters.
- Negative dimensions raise `RuntimeError`.
- Default NumPy `float64` input is typically downcast to `float32`; disable that with `jt.flag_scope(auto_convert_64_to_32=0)` or use an explicit dtype.
- `jt.random(shape, type='normal')` requests normal sampling; the default is uniform.
- Arithmetic follows NumPy-style broadcasting.

### Dtype control

```python
import jittor as jt
import numpy as np

arr = np.array([1.0, 2.0], dtype=np.float64)
with jt.flag_scope(auto_convert_64_to_32=0):
    x = jt.array(arr)
assert str(x.dtype) == 'float64'
```

## Broadcasting and matmul

Use normal arithmetic for broadcasted elementwise ops. For matrix products, `jt.matmul` follows these rules:

- `[n] @ [n] -> [1]`
- `[n, m] @ [m] -> [n]`
- `[n, m] @ [m, k] -> [n, k]`
- batched dimensions broadcast like NumPy; the last dim of `a` must match the second-to-last dim of `b`
- mismatches raise an assertion that includes both shapes

### Example

```python
import jittor as jt

a = jt.array([[1., 2., 3.]])
b = jt.array([1., 2., 3.])
assert (a + b).shape == (1, 3)

x = jt.array([[1., 2.]])
w = jt.array([[3.], [4.]])
assert jt.matmul(x, w).shape == (1, 1)
```

## Module and Function

### `Module`

- Subclass `jt.Module` and implement `execute`.
- Calling the instance runs `execute`.
- Any `Var` attribute on a `Module` is treated as a parameter unless you keep it private or manage it separately.
- `state_dict()` returns live parameters recursively; `save()` and `load()` are the local file helpers.

```python
import jittor as jt

class Tiny(jt.Module):
    def __init__(self):
        self.weight = jt.array([[2., 0.], [0., 2.]])
        self.bias = jt.array([1., -1.])
    def execute(self, x):
        return jt.matmul(x, self.weight) + self.bias
```

### `Function`

- Subclass `jt.Function` when you need a custom backward rule.
- Implement `execute` for forward and `grad` for backward.
- Store any values needed for backward on `self` during `execute`.
- `Function.apply` is the convenience classmethod form.
- In `grad`, return one gradient per input; return `None` for inputs that do not receive gradients.

```python
import jittor as jt
from jittor import Function

class ScaleAndShift(Function):
    def execute(self, x, scale, bias):
        self.scale = scale
        return x * scale + bias
    def grad(self, gout):
        return gout * self.scale, None, None
```

## Serialization basics

- `jt.save` and `jt.load` are the root helpers.
- `Module.save(path)` writes the module state dict; `Module.load(path)` reloads it.
- If the path looks like a checkpoint URL, Jittor downloads it before loading.
- `jt.load` understands Jittor pickle files and common PyTorch checkpoint extensions.
- A checksum mismatch usually means the file is truncated or corrupted; re-create or re-download it.

### Example

```python
import jittor as jt

payload = {"x": jt.array([1, 2, 3]), "n": 7}
jt.save(payload, "payload.pkl")
restored = jt.load("payload.pkl")
assert (restored["x"].data == [1, 2, 3]).all()
assert restored["n"] == 7
```
