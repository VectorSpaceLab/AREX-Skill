# Backends, Backend Classes, and Autodiff

## Purpose

Read this before using `be=...`, `tslearn.backend`, torch tensors, or
`SoftDTWLossPyTorch`. NumPy is the default correctness backend; PyTorch is an
optional tensor/autodiff backend, not a requirement for ordinary metric use.

## Selection rules

`instantiate_backend(*args)` scans its arguments in order:

1. If an argument is already a `Backend` instance, it is returned.
2. If the argument type or string representation contains `numpy`, the returned
   `Backend` wraps `NumPyBackend`.
3. If the argument type or string representation contains `torch`, the returned
   `Backend` wraps `PyTorchBackend`.
4. If no argument indicates NumPy or torch, the returned backend is NumPy.

Most metric functions call `instantiate_backend(be, s1, s2)` or an equivalent
variant. Consequences:

- Lists, Python scalars, and `be=None` normally select NumPy.
- NumPy arrays select NumPy even with `be=None`.
- Torch tensors select PyTorch even with `be=None`.
- Passing `be="pytorch"` forces PyTorch; passing `be="numpy"` forces NumPy.
- `"torch"` is accepted by the current backend selector, but the canonical
  `backend_string` is still `"pytorch"`. Prefer `"pytorch"` in user-facing
  code and use `"torch"` only when matching existing tslearn tests or code.
- Strings such as `"cuda"`, `"gpu"`, or an arbitrary invalid backend name do
  not select GPU; they fall back to NumPy because they do not contain `torch`.

## Backend objects and classes

- `Backend(data=None)` is the public wrapper. It forwards missing attributes to
  the concrete backend and exposes:
  - `.backend_string` (`"numpy"` or `"pytorch"`)
  - `.is_numpy` and `.is_pytorch`
  - `.get_backend()` for the concrete `NumPyBackend`/`PyTorchBackend`
  - `.set_backend(data)` to replace the concrete backend
- `select_backend(data)` is the lower-level selector that returns the concrete
  backend class instance.
- `cast(data, array_type="numpy")` converts to NumPy, PyTorch, or list; use it
  only in support code/tests, not as a substitute for validating shapes.
- `NumPyBackend` wraps NumPy/SciPy/scikit-learn distance and array functions.
- `PyTorchBackend` wraps torch tensor operations and `torch.cdist` for the
  supported distance strings (`"euclidean"`, `"sqeuclidean"`, and Minkowski
  where implemented).

Quick backend sanity check:

```python
from tslearn.backend import instantiate_backend

be = instantiate_backend("pytorch")   # requires torch installed
assert be.backend_string == "pytorch"
assert be.is_pytorch

assert instantiate_backend("not-a-backend").backend_string == "numpy"
```

## When NumPy is enough

Use NumPy/list inputs and leave `be=None` for:

- Scalar distances and paths: DTW, Soft-DTW, GAK, LCSS, Fréchet, CTW.
- `cdist_*` matrices and warping masks.
- Barycenters: Euclidean, DBA, and Soft-DTW barycenter computations return
  NumPy arrays and are documented as CPU-sufficient here.
- `tslearn.metrics.performance` metrics.
- Verifying metric parameter choices before plugging them into estimators.

NumPy is also the easiest backend for custom metric strings because it delegates
string metrics to scikit-learn/scipy-style pairwise distances.

## When PyTorch is needed

Use PyTorch only when the task requires one of these:

- Input/output tensors should remain torch tensors.
- The downstream calculation needs `backward()` through `dtw` or `soft_dtw`.
- The user needs `SoftDTWLossPyTorch` as a batched neural-network loss.
- A custom distance callable is written in torch and should participate in
  autograd.

Example for top-level metric autodiff:

```python
import torch
from tslearn.metrics import soft_dtw

x = torch.tensor([[1.0], [2.0], [3.0]], requires_grad=True)
y = torch.tensor([[3.0], [4.0], [-3.0]])
loss = soft_dtw(x, y, gamma=1.0, be="pytorch")
loss.backward()
assert x.grad is not None
```

Use Soft-DTW rather than hard DTW for training-style objectives when possible.
DTW can expose a tensor gradient through the selected path, but it remains a
non-smooth hard-min objective around path changes.

## SoftDTWLossPyTorch

`SoftDTWLossPyTorch(gamma=1.0, normalize=False, dist_func=None,
global_constraint=None, sakoe_chiba_radius=None, itakura_max_slope=None)` is a
PyTorch `nn.Module`. It expects:

- `x`: tensor shape `(batch_size, length_x, dim)`
- `y`: tensor shape `(batch_size, length_y, dim)`
- equal batch size and feature dimension
- `dist_func(x, y)` returning a tensor shape `(batch_size, length_x, length_y)`
  if you override the default squared Euclidean distance

Pattern:

```python
import torch
from tslearn.metrics import SoftDTWLossPyTorch

x = torch.zeros((2, 3, 1), requires_grad=True)
y = torch.ones((2, 4, 1))
criterion = SoftDTWLossPyTorch(gamma=1.0, normalize=True)
loss = criterion(x, y).mean()
loss.backward()
assert x.grad.shape == x.shape
```

Caveats:

- The module raises a clear `ValueError` if torch is not installed.
- Keep `gamma` strictly positive for this training loss. Top-level
  `soft_dtw(..., gamma=0)` has a special squared-DTW fallback, but that is not
  a training-loss recommendation.
- `normalize=True` computes the Soft-DTW divergence by evaluating `xy`, `xx`,
  and `yy`, so it is about three times the base loss cost.
- Keep custom `dist_func` code in torch; using NumPy inside it detaches the
  graph and breaks gradients.

## CPU correctness vs CUDA acceleration

This sub-skill treats CPU as sufficient. A machine may have CUDA and still need
CPU-only validation for reproducible correctness. Do not infer speedups from
`torch.cuda.is_available()` alone:

- Top-level PyTorch backend metrics use torch tensors and can participate in
  autograd, but actual speed depends on tensor device, length, dimensions, and
  dynamic-programming structure.
- `SoftDTWLossPyTorch` preserves torch autograd but performs its dynamic
  programming core through CPU-side arrays before returning tensors to the
  original device. CUDA tensors can incur transfer overhead.
- Always run a tiny smoke, then profile the actual workload if acceleration is
  a user requirement.

Use the bundled helper for a quick backend check. From the `metrics-backends/`
sub-skill directory, run:

```bash
python scripts/metrics_smoke.py dtw --backend numpy
python scripts/metrics_smoke.py dtw --backend pytorch
python scripts/metrics_smoke.py softdtw-loss
```
