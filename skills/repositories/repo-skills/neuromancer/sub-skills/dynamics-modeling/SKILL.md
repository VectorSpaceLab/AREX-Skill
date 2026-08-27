---
name: dynamics-modeling
description: "Construct and route NeuroMANCER neural blocks, continuous and
  stochastic dynamics, physics-informed models, integrators, interpolation, and
  system-identification components without mixing in training or control-loop
  concerns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Dynamics modeling

Use this skill when the task is to **construct, inspect, or compose a model** of a dynamical system in NeuroMANCER. Keep the runtime model self-contained: use package imports and the contracts in the bundled references, not repository-relative imports or example files.

## Route the request

- Use [`references/api-reference.md`](references/api-reference.md) for stable imports, signatures, tensor shapes, and optional backends.
- Use [`references/workflows.md`](references/workflows.md) for build recipes: neural state-space/ODE models, named or SINDy systems, networked physics, DAE operator splitting, PINN residuals, function encoders, and interpolation/SDE paths.
- Use [`references/troubleshooting.md`](references/troubleshooting.md) when dimensions, autograd, solver options, device/dtype, or optional dependencies are involved.
- Run `scripts/dynamics_smoke.py --help`; run `scripts/dynamics_smoke.py --run` in an environment where the package's ODE dependencies are installed.

## Core routing rules

1. **Choose the tensor contract before choosing the class.** Ordinary blocks consume rank-2 `[batch, features]` tensors. `Block.forward(*inputs)` concatenates multiple rank-2 inputs along the last axis. Sequence wrappers have their own `[batch, time, features]` contract; see the API reference.
2. **Separate state width from input width.** An autonomous RHS maps `[B, nx] -> [B, nx]`. A non-autonomous RHS is constructed with `insize=nx+nu, outsize=nx`, but is called as `rhs(x, u)` with `[B, nx]` and `[B, nu]` tensors.
3. **Use `Euler`, `RK2`, or `RK4` for transparent one-step CPU integration; use `DiffEqIntegrator` for torchdiffeq methods and adjoint differentiation.** Use the multistep and second-order families only with their specialized state layouts.
4. **Treat SDEs, PINNs, and DAE models as explicit advanced paths.** SDE integration requires TorchSDE. PINN coordinates must retain a differentiable autograd graph. DAE examples use algebraic-update then differential-update composition rather than a hidden generic solver.
5. **Do not put losses, datasets, trainers, or control rollouts here.** Route loss/data/training setup to `symbolic-problems` or `data-training`, and closed-loop/system simulation to `control-simulation`. Route structured-map registry selection or native extensions to `structured-operators`.
6. **Do not promise GPU or native-extension coverage.** The CPU construction and shape paths are the baseline; TorchSDE/TorchDiffEq, CUDA, and native structured operators are separately verified capabilities.

## Minimal construction shape

```python
import torch
from neuromancer.modules.blocks import MLP
from neuromancer.dynamics.integrators import RK4

nx, nu = 2, 1
rhs = MLP(nx + nu, nx, linear_map=torch.nn.Linear,
          nonlin=torch.nn.Tanh, hsizes=[16, 16])
stepper = RK4(rhs, h=0.05)
x = torch.zeros(8, nx)
u = torch.zeros(8, nu)
x_next = stepper(x, u)       # [8, 2]
```

For complete model variants, shape checks, and the model-versus-training boundary, follow the linked references rather than expanding this router.
