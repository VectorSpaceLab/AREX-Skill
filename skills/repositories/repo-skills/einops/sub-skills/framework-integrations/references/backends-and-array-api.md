# Backends and Array API

## Purpose

Read this when a task asks whether `einops` supports a tensor framework, how
backend dispatch is selected, how to use the Array API namespace, or whether a
CPU smoke check proves GPU/accelerator behavior.

## Backend Dispatch Model

`einops` keeps backend imports lazy. The public functions inspect the runtime
tensor object, then search registered backend classes. A backend is only tried
when its framework module is already present in `sys.modules`; this avoids
importing heavy frameworks that the user did not install or import.

Practical consequence:

```python
import torch
from einops import rearrange

x = torch.randn(2, 3, 4)
y = rearrange(x, "batch channel time -> batch time channel")
```

If the user constructs a tensor through a framework but never imports that
framework in the process, or passes an unsupported wrapper type, `einops` can
raise a `RuntimeError` containing `Tensor type unknown to einops`.

## Supported Backend Names From Source

The source backend classes define these framework names. For lazy dispatch, the
listed framework module must already be imported in the Python process and the
object must be the framework's native tensor type.

| Backend name | Import first | Typical tensor family | Layer module | Notes |
| --- | --- | --- | --- | --- |
| `numpy` | `import numpy` | `numpy.ndarray` | None | Baseline imperative backend; NumPy 2.x can also use the Array API path. |
| `jax` | `import jax` or `import jax.numpy` | JAX arrays | Use Flax layers for model modules | Uses `jax.numpy`; install JAX separately. |
| `torch` | `import torch` | `torch.Tensor` | `einops.layers.torch` | Backend construction imports torch-specific compile registration. |
| `cupy` | `import cupy` | CuPy arrays | None | Optional GPU array package; import success is not CUDA verification. |
| `tensorflow` | `import tensorflow` | Eager `tf.Tensor`/`tf.Variable` | `einops.layers.tensorflow` | Uses TensorFlow operations; symbolic shape handling is backend-specific. |
| `tensorflow.keras` | `import tensorflow` / `tf.keras` | Keras symbolic tensors | `einops.layers.keras` | Distinct symbolic backend; use `keras_custom_objects` for Keras loading. |
| `oneflow` | `import oneflow` | OneFlow tensors | `einops.layers.oneflow` | Optional community backend and layer family. |
| `paddle` | `import paddle` | Paddle tensors | `einops.layers.paddle` | Optional community backend and layer family. |
| `tinygrad` | `import tinygrad` | tinygrad tensors | None | Optional functional backend. |
| `pytensor` | `import pytensor` | PyTensor symbolic variables | None | Optional symbolic backend. |
| `mlx.core` | `import mlx.core` | MLX arrays | None | Optional MLX backend; do not claim Apple accelerator verification without a device smoke. |

README-supported ordinary framework names include NumPy, PyTorch, TensorFlow,
JAX, CuPy, Flax, Paddle, OneFlow, Tinygrad, and PyTensor. README-supported
Array API-compatible examples include NumPy >= 2.0, MLX, pydata/sparse >= 0.15,
cubed, ndonnx, JAX, CuPy, and Dask via array-api-compat. Treat every package in
those lists as optional unless the user's environment has already installed it.

## Functional API Versus Array API Namespace

Use the top-level functions for known backend tensor types:

```python
from einops import rearrange, reduce, repeat, pack, unpack, einsum
```

Use `einops.array_api` when the object exposes `__array_namespace__` and the task
explicitly targets Array API behavior:

```python
from einops import array_api as E

result = E.rearrange(xp_array, "batch channel time -> batch time channel")
packed, ps = E.pack([tokens, class_token], "batch * channel")
```

Array API functions in this source cover:

- `reduce(tensor_or_list, pattern, reduction, **axes_lengths)`
- `rearrange(tensor_or_list, pattern, **axes_lengths)`
- `repeat(tensor_or_list, pattern, **axes_lengths)`
- `asnumpy(tensor)` via DLPack/NumPy
- `pack(tensors, pattern)`
- `unpack(tensor, packed_shapes, pattern)`

Array API backends may differ in available reductions, DLPack support, dtype
behavior, and array creation utilities. Start with the bundled smoke script for
an installed provider before claiming compatibility.

## Optional Dependencies and Environments

`einops` itself has no runtime dependencies in project metadata. Optional tensor
frameworks are installed by the user's project, not by `einops`. Avoid telling
users to install every optional framework. Instead:

1. Identify the tensor object or model framework named by the task.
2. Install or verify only that framework and its normal CPU/GPU variant.
3. Import the framework before calling `einops`.
4. Run a tiny shape operation and one failure case.
5. For framework layers, use the framework-specific module and run a minimal
   forward pass if the framework is installed.

## Accelerator Honesty

`einops` delegates actual numerical work to the tensor framework. Therefore:

- A NumPy or CPU torch smoke validates pattern semantics, not CUDA/ROCm/MPS.
- If a user asks for GPU behavior, verify the framework itself on the target
  device, then run a tiny `einops` operation on a tensor already on that device.
- Do not install GPU packages merely because the host has a GPU if the task only
  needs package inspection or CPU-safe usage guidance.
- Do not claim `einops` accelerator support was verified unless the actual
  framework/device tensor was used in a runtime check.

Example CUDA-honest check when PyTorch CUDA is already installed:

```python
import torch
from einops import rearrange

assert torch.cuda.is_available()
x = torch.arange(24, device="cuda").reshape(2, 3, 4)
y = rearrange(x, "b c t -> b t c")
assert y.device.type == "cuda"
```

## Backend Test Selection

Repository-native tests use `EINOPS_TEST_BACKENDS` and backend names such as
`numpy`, `torch`, `tensorflow`, `jax`, `pytensor`, and `mlx.core`. See
[`repo-development`](../../repo-development/SKILL.md) for maintainer test runner
guidance. For user package usage, prefer a direct import and tiny operation over
running the repository's full optional backend matrix.
