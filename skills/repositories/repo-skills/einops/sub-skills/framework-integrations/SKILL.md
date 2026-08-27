---
name: framework-integrations
description: "Use optional einops backends, Array API functions, framework
  layers, EinMix, and framework-specific diagnostics without overclaiming
  accelerator support."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Framework Integrations

Use this sub-skill when a task asks how `einops` works with tensor libraries,
Array API objects, framework layers, `EinMix`, torch scripting/compilation, or
missing optional backend diagnostics. Core shape recipes stay in
[`tensor-operations`](../tensor-operations/SKILL.md); named `einsum`, `pack`,
and `unpack` stay in
[`named-einsum-and-packing`](../named-einsum-and-packing/SKILL.md).

## When To Load

- A user has a NumPy, PyTorch, TensorFlow/Keras, JAX, CuPy, Paddle, OneFlow,
  PyTensor, MLX, tinygrad, or Array API tensor and wants the right `einops`
  entry point.
- A user asks whether `einops` supports a backend, symbolic tensors, framework
  layers, gradients, tracing, scripting, or `torch.compile`.
- A user wants `einops.layers.torch.Rearrange`, `einops.layers.tensorflow.Reduce`,
  Flax modules, Paddle/OneFlow layers, or `EinMix` in model code.
- A user hits `Tensor type unknown to einops`, missing optional framework
  imports, Keras serialization questions, Array API limitations, or accelerator
  confusion.

## Boundary Rules

Stay here for framework integration. Route away for:

- Plain reshapes, reductions, repeats, `parse_shape`, and pattern grammar:
  [`tensor-operations`](../tensor-operations/SKILL.md).
- Named-axis contractions or reversible packing:
  [`named-einsum-and-packing`](../named-einsum-and-packing/SKILL.md).
- Repository CI, package tests, notebook/docs checks, or release workflows:
  [`repo-development`](../repo-development/SKILL.md).

## Operational Guidance

1. Start from the public package install:

   ```bash
   pip install einops
   ```

   `einops` itself declares no runtime dependencies. Install tensor frameworks
   separately, in versions appropriate for the user's project.

2. Import the framework before passing its tensors to `einops`. Backends are
   lazy and are only registered when their framework module is already imported.

   ```python
   import torch
   from einops import rearrange

   x = torch.randn(2, 3, 4)
   y = rearrange(x, "batch channel time -> batch time channel")
   ```

3. Use the regular top-level functions for most tensor objects. Use
   `einops.array_api` only when the tensor follows the Python Array API standard
   and exposes `__array_namespace__`.

4. In model definitions, prefer framework layers when the transform should be a
   serializable or traceable layer:

   ```python
   from einops.layers.torch import Rearrange, Reduce
   ```

5. Use `EinMix` when a linear layer plus rearrangement/einsum weight management
   is the real abstraction, not merely when a simple reshape is needed.

6. Treat accelerator support honestly. `einops` delegates tensor computation to
   the installed framework. A CPU smoke check proves pattern logic, not CUDA,
   ROCm, MPS, or vendor accelerator runtime.

## Reference Map

- [`references/backends-and-array-api.md`](references/backends-and-array-api.md):
  supported backend names, lazy dispatch model, Array API variants, optional
  dependency policy, and accelerator honesty.
- [`references/layers-and-einmix.md`](references/layers-and-einmix.md): layer
  imports, framework-specific constructor patterns, `EinMix` signatures,
  restrictions, and model recipes.
- [`references/troubleshooting.md`](references/troubleshooting.md): missing
  optional dependencies, unknown tensor type, Array API problems, TensorFlow
  layer-version notes, torch compile/script behavior, and `EinMix` errors.
- [`scripts/array_api_smoke.py`](scripts/array_api_smoke.py): safe Array API
  diagnostic adapted from repository tests; runs with NumPy 2.x by default.
- [`scripts/layer_smoke.py`](scripts/layer_smoke.py): safe layer/`EinMix`
  diagnostic with pure-Python default checks and optional framework probes.

## Quick Diagnostics

Check a framework tensor failure:

```python
import torch  # or tensorflow, jax.numpy, cupy, paddle, oneflow, pytensor, mlx.core
from einops import rearrange

# If this still raises "Tensor type unknown to einops", inspect the tensor type
# and whether the framework import matches the object being passed.
```

Run bundled checks after installing public dependencies:

```bash
python sub-skills/framework-integrations/scripts/array_api_smoke.py --help
python sub-skills/framework-integrations/scripts/array_api_smoke.py
python sub-skills/framework-integrations/scripts/layer_smoke.py --help
python sub-skills/framework-integrations/scripts/layer_smoke.py
python sub-skills/framework-integrations/scripts/layer_smoke.py --framework torch
```

If an optional framework is absent, the scripts report a clear skip/failure
message instead of assuming the source checkout has that framework installed.

## Evidence Summary

This sub-skill distills public evidence from `README.md`, `einops/_backends.py`,
`einops/_torch_specific.py`, `einops/array_api.py`, `einops/layers/*`,
`einops/tests/test_array_api.py`, `einops/tests/test_layers.py`,
`einops/tests/test_other.py`, and the `EinMix` tutorial headings and examples.
Installed-package inspection verified core imports and signatures; optional
framework runtime verification is deliberately left to the user's installed
framework environment.
