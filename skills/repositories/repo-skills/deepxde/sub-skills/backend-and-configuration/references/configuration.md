# DeepXDE configuration APIs

Apply configuration immediately after importing DeepXDE and before constructing data objects, networks, or models. Backend selection itself must happen earlier, before `import deepxde`.

```python
import os
os.environ.setdefault("DDE_BACKEND", "pytorch")

import deepxde as dde

dde.config.set_default_float("float32")
dde.config.set_random_seed(1234)
dde.config.set_default_autodiff("reverse")
```

This construction verified the PyTorch CPU path. The notes below include optional TensorFlow, JAX, PaddlePaddle, GPU, and Horovod behavior from DeepXDE docs and source; verify those paths before relying on them.

## Common configuration sequence

| Step | API | Typical values | When to call | Notes |
|---|---|---|---|---|
| 1 | Backend selection | `DDE_BACKEND=pytorch` | Before `import deepxde` | Not a `dde.config` API. See [backend-selection.md](backend-selection.md). |
| 2 | `dde.config.set_default_float(value)` | `"float32"`, `"float64"`, `"float16"`, `"mixed"` | Before creating tensors/networks | Default is `float32`. Mixed precision is backend-limited. |
| 3 | `dde.config.set_random_seed(seed)` | integer | Before sampling/training | Sets Python, NumPy, and backend seeds and enables deterministic behavior where supported; determinism can reduce performance. |
| 4 | `dde.config.set_default_autodiff(value)` | `"reverse"`, `"forward"` | Before defining derivative-heavy residuals | Default is reverse mode. Use forward mode when a specific workflow requires it. |
| 5 | `dde.config.enable_xla_jit(mode=True)` / `disable_xla_jit()` | booleans | Before compiling/running TensorFlow/JAX workflows | Backend restrictions apply. PyTorch and Paddle do not support DeepXDE XLA config. |
| 6 | `dde.config.set_parallel_scaling(scaling_mode)` | `"weak"`, `"strong"` | In Horovod/MPI TensorFlow-1.x scripts | Only relevant to data-parallel Horovod execution. |

## `set_default_float(value)`

Supported values are:

- `"float32"`: default and safest baseline.
- `"float64"`: useful for numerical accuracy, slower and more memory-intensive.
- `"float16"`: lower precision; use only when the backend and problem tolerate it.
- `"mixed"`: mixed precision using float16/float32 behavior. DeepXDE source supports this for TensorFlow 2.x and PyTorch; other backends raise an error.

Backend effects:

- TensorFlow backends call `tf.keras.backend.set_floatx(value)`.
- PyTorch calls `torch.set_default_dtype(...)`; for `"mixed"`, DeepXDE stores the default real precision as float32 while using mixed-precision workflow assumptions.
- Paddle calls `paddle.set_default_dtype(value)`.
- JAX float64 support is constrained by JAX's own 64-bit configuration; DeepXDE source notes that JAX float64 may be truncated to float32 unless JAX is separately configured.

Safe pattern:

```python
try:
    dde.config.set_default_float("float64")
except ValueError as exc:
    raise RuntimeError(f"Requested float mode is unsupported by this backend: {exc}")
```

## `set_random_seed(seed)`

`dde.config.set_random_seed(seed)` seeds Python `random`, NumPy, and the selected backend:

- `tensorflow.compat.v1`: sets deterministic TensorFlow environment flags and `tf.set_random_seed(seed)`.
- `tensorflow`: sets deterministic TensorFlow environment flags and `tf.random.set_seed(seed)`.
- `pytorch`: calls `torch.manual_seed(seed)`.
- `jax`: updates DeepXDE's JAX random seed variable.
- `paddle`: calls `paddle.seed(seed)`.

Use this for debugging and reproducibility. Do not promise bitwise reproducibility across different hardware, backend versions, or GPU kernels.

## `set_default_autodiff(value)`

DeepXDE accepts:

```python
dde.config.set_default_autodiff("reverse")
dde.config.set_default_autodiff("forward")
```

Reverse mode is the default. Forward mode can help in some derivative-heavy formulations, but backend and feature coverage can differ. If a PDE residual or operator-learning workflow fails with autodiff errors, retry the default reverse mode before changing the mathematical formulation.

DeepXDE's README also mentions zero coordinate shift (ZCS) as an automatic differentiation method. ZCS operator workflows are specialized; route those tasks to the operator-learning sub-skill.

## XLA JIT

Initial `dde.config.xla_jit` behavior depends on backend:

- TensorFlow 1.x and TensorFlow 2.x: enabled by default only when a GPU is available and Horovod is not active.
- JAX: always uses XLA.
- PyTorch and Paddle: DeepXDE's XLA config is unsupported.

API behavior:

```python
dde.config.enable_xla_jit(True)
dde.config.disable_xla_jit()
```

Restrictions enforced by DeepXDE source:

- `tensorflow.compat.v1`: enabling XLA without GPU raises `ValueError`.
- `tensorflow`: disabling uses a TensorFlow-specific `None` mode internally.
- `jax`: disabling raises `ValueError` because JAX always uses XLA.
- `pytorch` and `paddle`: enabling raises `ValueError`.

For a CPU-safe PyTorch workflow, leave XLA alone.

## Parallel scaling, Horovod, and MPI

DeepXDE data-parallel training is documented for Horovod with the `tensorflow.compat.v1` backend and random collocation-point sampling. The docs show execution like:

```bash
horovodrun -np 2 -H localhost:2 python script.py
```

DeepXDE source activates Horovod when MPI environment variables such as `OMPI_COMM_WORLD_SIZE` are present. For `tensorflow.compat.v1`, it initializes Horovod, sets weak scaling by default when world size is greater than 1, and uses `mpi4py` for the communicator. If MPI variables are present with another backend, DeepXDE raises `NotImplementedError` for Horovod parallel training.

Use:

```python
dde.config.set_parallel_scaling("weak")
dde.config.set_parallel_scaling("strong")
```

- `"weak"`: increase problem size proportionally with number of workers.
- `"strong"`: keep problem size fixed and split work across workers.

This generated skill did not verify Horovod, MPI, multiple processes, or GPUs. Treat parallel execution as optional and environment-specific.

## GPU/default-device behavior

GPU support depends on the installed backend package and drivers. This construction did not verify any GPU path.

- TensorFlow backends set `TF_FORCE_GPU_ALLOW_GROWTH=true` on backend import to avoid taking all GPU memory up front.
- PyTorch backend: if `torch.cuda.is_available()` is true, DeepXDE sets CUDA as the default device. On macOS with MPS available, DeepXDE attempts `torch.set_default_device("mps")` and falls back if the test run fails.
- Paddle backend: if Paddle is compiled with CUDA, DeepXDE sets the Paddle default device to GPU.
- JAX device behavior follows the installed JAX/JAXLIB build and platform configuration.

If a CPU-only workflow unexpectedly tries to place tensors on GPU, inspect backend package/device visibility and run:

```bash
python scripts/check_backend.py --backend pytorch --json
```

If a GPU is required, make the requirement explicit:

```bash
python scripts/check_backend.py --backend pytorch --require-gpu
```
