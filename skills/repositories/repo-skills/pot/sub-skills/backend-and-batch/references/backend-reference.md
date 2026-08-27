# POT backend reference

Use this reference when a POT workflow must preserve a non-NumPy array type, diagnose backend discovery, or safely convert between array libraries. The minimum verified runtime for this skill is NumPy only: optional PyTorch, JAX, TensorFlow, and CuPy behavior must be treated as user-environment dependent until the user verifies it locally.

## Quick commands

```bash
# Print backend implementations detected by the installed POT import and run no solver work.
python scripts/backend_batch_smoke.py --case backends

# Instantiate backend objects too. This may import or initialize optional GPU libraries.
python scripts/backend_batch_smoke.py --case backends --instantiate-backends

# Require an optional backend and fail with an explicit install/disable message if unavailable.
python scripts/backend_batch_smoke.py --case backends --require-optional torch
python scripts/backend_batch_smoke.py --case backends --require-optional jax
python scripts/backend_batch_smoke.py --case backends --require-optional tensorflow
python scripts/backend_batch_smoke.py --case backends --require-optional cupy
```

## Verified public signatures and defaults

| API | Signature/defaults verified for POT 0.9.7.post1 | Operating notes |
| --- | --- | --- |
| `ot.backend.get_backend(*args)` | variadic | Ignores `None`, requires at least one non-`None` argument, and returns the backend instance matching all arrays. Mixed array libraries raise `ValueError`; unknown Python scalars alone also raise `ValueError`. |
| `ot.backend.get_backend_list()` | no arguments | Returns instantiated backend objects for every implementation registered by the current POT import. Instantiation can have side effects for optional GPU frameworks, so prefer this only when you need backend objects. |
| `ot.backend.get_available_backend_implementations()` | no arguments | Returns registered backend classes without forcing instances. Use it when you only need names such as `numpy`, `torch`, `jax`, `tensorflow`, or `cupy`. |
| `ot.backend.to_numpy(*args)` | variadic | Converts one backend array to a NumPy array, or returns a list of NumPy arrays for multiple inputs. For differentiable frameworks this is for logging/validation, not for preserving gradients. |

Backend class names exposed by POT include `NumpyBackend`, `TorchBackend`, `JaxBackend`, `TensorflowBackend`, `CupyBackend`, and the base `Backend`. Every backend instance has `__name__`, `__type__`, `from_numpy`, `to_numpy`, `detach`, numerical array constructors, and dtype/device helpers. Use `nx = ot.backend.get_backend(array1, array2, ...)` and then use `nx` methods instead of hard-coding `np` operations inside backend-generic code.

## Backend selection contract

1. Build all POT inputs with the same array backend before calling a POT solver.
2. Let POT infer the backend with `get_backend(a, b, M)` when every non-`None` argument is already an array of that backend.
3. Use `nx.from_numpy(array, type_as=template)` to convert a NumPy value to the same dtype/device as a template backend array.
4. Use `ot.backend.to_numpy(result.plan, result.value)` only after the solver call for validation, printing, serialization, or comparison against NumPy fixtures.
5. Do not mix SciPy sparse matrices with Torch tensors, or Torch sparse tensors with NumPy arrays; SciPy sparse belongs to the NumPy backend and Torch sparse belongs to the Torch backend.

### Minimal NumPy pattern

```python
import numpy as np
import ot
from ot.backend import get_backend, to_numpy

M = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=float)
a = np.array([0.5, 0.5], dtype=float)
b = np.array([0.5, 0.5], dtype=float)

nx = get_backend(a, b, M)
assert nx.__name__ == "numpy"
res = ot.solve(M, a, b, n_threads=1)
plan_np, value_np = to_numpy(res.plan, res.value)
```

### Optional PyTorch pattern

Only use this when PyTorch is installed and verified in the user's environment.

```python
import numpy as np
import torch
import ot
from ot.backend import get_backend

M_np = np.array([[0.0, 1.0], [1.0, 0.0]], dtype="float64")
template = torch.ones(1, dtype=torch.float64, device="cpu")
nx = get_backend(template)

M = nx.from_numpy(M_np, type_as=template).requires_grad_(True)
a = torch.tensor([0.5, 0.5], dtype=template.dtype, device=template.device, requires_grad=True)
b = torch.tensor([0.5, 0.5], dtype=template.dtype, device=template.device, requires_grad=True)

res = ot.solve(M, a, b, reg=0.5, grad="envelope")
res.value.backward()
```

For CUDA tensors, create the template on the intended CUDA device and keep every input on that device. A GPU being visible to Python is not enough: the solver uses the backend and device of the arrays you pass.

### Optional JAX pattern

Only use this when JAX and JAXlib are installed and verified locally.

```python
import jax.numpy as jnp
import ot
from ot.backend import get_backend

M = jnp.array([[0.0, 1.0], [1.0, 0.0]])
a = jnp.array([0.5, 0.5])
b = jnp.array([0.5, 0.5])
assert get_backend(M, a, b).__name__ == "jax"
res = ot.solve(M, a, b, reg=0.5, grad="envelope")
```

If JAX GPU memory preallocation is a problem, set the appropriate JAX environment controls before Python imports JAX/POT; this is a JAX runtime concern, not a POT solver parameter.

### Optional TensorFlow pattern

TensorFlow support in POT relies on TensorFlow's NumPy API. Enable it before creating TensorFlow arrays for POT calls.

```python
from tensorflow.python.ops.numpy_ops import np_config
np_config.enable_numpy_behavior()

import tensorflow as tf
import tensorflow.experimental.numpy as tnp
import ot
from ot.backend import get_backend

M = tnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=tnp.float64)
a = tnp.array([0.5, 0.5], dtype=tnp.float64)
b = tnp.array([0.5, 0.5], dtype=tnp.float64)
assert get_backend(M, a, b).__name__ == "tensorflow"
res = ot.solve(M, a, b, reg=0.5, grad="envelope")
```

If TensorFlow tries to claim too much GPU memory, configure TensorFlow memory growth before running large POT calls.

### Optional CuPy pattern

Only use this when a CUDA-compatible CuPy package is installed and verified locally. POT's `backend-cupy` extra intentionally does not install CuPy because the correct CuPy package depends on the user's CUDA stack.

```python
import cupy as cp
import ot
from ot.backend import get_backend

M = cp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=cp.float64)
a = cp.asarray([0.5, 0.5], dtype=cp.float64)
b = cp.asarray([0.5, 0.5], dtype=cp.float64)
assert get_backend(M, a, b).__name__ == "cupy"
res = ot.solve(M, a, b, reg=0.5, grad="detach")
```

Install a CuPy variant that matches the CUDA runtime, such as a conda-forge CuPy build or the appropriate `cupy-cudaXX` wheel. If CuPy import fails or the CUDA runtime is mismatched, either repair the CuPy installation or disable it for POT import as shown below.

## Optional dependency routes

| Backend | Package route | Verification status in the minimum skill runtime |
| --- | --- | --- |
| NumPy | Base POT install (`pip install POT` or conda package) | Verified. |
| PyTorch | `pip install "POT[backend-torch]"` or install compatible `torch` first | Optional; not verified by the minimum runtime. |
| JAX | `pip install "POT[backend-jax]"` or compatible `jax`/`jaxlib` install | Optional; not verified by the minimum runtime. |
| TensorFlow | `pip install "POT[backend-tf]"` or compatible `tensorflow` install | Optional; not verified by the minimum runtime. |
| CuPy | Install a CUDA-compatible CuPy package separately | Optional; not verified by the minimum runtime. |

Do not claim that an optional backend works until an import probe and a tiny solver smoke check have passed in the user's environment.

## Disable optional backend imports

POT checks these environment variables at import time. Set them before Python imports `ot`.

| Environment variable | Effect |
| --- | --- |
| `POT_BACKEND_DISABLE_PYTORCH=1` | Do not import/register the PyTorch backend. |
| `POT_BACKEND_DISABLE_JAX=1` | Do not import/register the JAX backend. |
| `POT_BACKEND_DISABLE_CUPY=1` | Do not import/register the CuPy backend. |
| `POT_BACKEND_DISABLE_TENSORFLOW=1` | Do not import/register the TensorFlow backend. |

Examples:

```bash
# Disable every optional backend for a pure NumPy run.
POT_BACKEND_DISABLE_PYTORCH=1 \
POT_BACKEND_DISABLE_JAX=1 \
POT_BACKEND_DISABLE_CUPY=1 \
POT_BACKEND_DISABLE_TENSORFLOW=1 \
python scripts/backend_batch_smoke.py --case all

# Keep Torch available but prevent TensorFlow/CuPy/JAX imports.
POT_BACKEND_DISABLE_JAX=1 \
POT_BACKEND_DISABLE_CUPY=1 \
POT_BACKEND_DISABLE_TENSORFLOW=1 \
python - <<'PY'
import ot
from ot.backend import get_available_backend_implementations
print([impl.__name__ for impl in get_available_backend_implementations()])
PY
```

## Validation checklist

Before trusting a backend-specific POT result:

1. Print `get_backend(*inputs).__name__` and confirm it is the intended backend.
2. Confirm every tensor has the same dtype and device class when the backend supports devices.
3. Run `python scripts/backend_batch_smoke.py --case backends` to confirm POT registered the expected backend implementation.
4. Run a tiny solver with that backend; for optional backends, compare `to_numpy(result.plan)` or `to_numpy(result.value)` against a NumPy fixture.
5. For differentiable workflows, choose a gradient mode deliberately and verify a gradient exists on the intended tensor before scaling the problem.
