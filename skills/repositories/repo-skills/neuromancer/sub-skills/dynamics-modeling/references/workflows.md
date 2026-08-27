# Dynamics modeling workflows

These recipes are intentionally bounded: they construct and validate models, but do not launch long training, download datasets, or run control loops. Add data and losses through the sibling routes only after the model contract is correct.

## 1. Build and check a neural state-space or neural ODE stepper

First decide whether the learned object is discrete (`SSM`) or a continuous-time RHS (`ODESystem`/a block wrapped in an integrator).

### Discrete SSM

```python
import torch
from neuromancer.modules.blocks import MLP
from neuromancer.dynamics.ode import SSM

nx, nu = 3, 2
fx = MLP(nx, nx, linear_map=torch.nn.Linear,
         nonlin=torch.nn.Tanh, hsizes=[16])
fu = MLP(nu, nx, linear_map=torch.nn.Linear,
         nonlin=torch.nn.Tanh, hsizes=[16])
ssm = SSM(fx, fu, nx=nx, nu=nu)
x = torch.randn(5, nx)
u = torch.randn(5, nu)
x_next = ssm(x, u)
assert x_next.shape == (5, nx)
```

`SSM` adds `fd(d)` only if it was constructed with an `fd` module and a disturbance is passed. Keep `d` rank 2 and width `nd`.

### Autonomous or input-driven neural ODE

A normal MLP is a valid RHS because it already has `in_features` and `out_features`:

```python
from neuromancer.modules.blocks import MLP
from neuromancer.dynamics.integrators import RK4

nx, nu = 2, 1
rhs = MLP(nx + nu, nx, linear_map=torch.nn.Linear,
          nonlin=torch.nn.Tanh, hsizes=[32, 32])
step = RK4(rhs, h=0.02)
x = torch.zeros(8, nx)
u = torch.zeros(8, nu)
x_next = step(x, u)
assert x_next.shape == (8, nx)
```

The block sees `x` and `u` as separate arguments; `Block.forward` concatenates them. For an autonomous RHS, construct `MLP(nx, nx, ...)` and call `step(x)`. To expose a model to a NeuroMANCER computation graph, wrap the stepper in a `Node` with keys such as `['xn', 'U'] -> ['xn']`; graph keys, rollout horizon, losses, and data belong to the symbolic/data/training routes.

`DiffEqIntegrator(rhs, h=dt, method='rk4')` is a drop-in alternative when TorchDiffEq and its adjoint path are available. It returns one final state over `[0, h]`, not the whole time trajectory. Use the direct fixed-step classes when an optional solver dependency is unavailable or when a transparent differentiable update is sufficient.

## 2. Use named ODE systems, hybrid models, and SINDy

Named systems encode a known equation with trainable or fixed parameters. Inspect `in_features` and `out_features` before preparing tensors:

```python
from neuromancer.dynamics.ode import VanDerPolControl, LorenzParam

controlled = VanDerPolControl()     # total insize=3, state outsize=2
x = torch.randn(4, 2)
u = torch.randn(4, 1)
dx = controlled(x, u)                # [4, 2]

lorenz = LorenzParam()               # autonomous 3-state system
x3 = torch.randn(4, lorenz.in_features)
dx3 = lorenz(x3)                     # [4, 3]
```

For a hybrid system, make the black-box block match the assertion in the chosen class. For example, `LotkaVolterraHybrid` and `BrusselatorHybrid` expect a block with `in_features=2` and `out_features=1` and return a known two-state derivative. The hybrid block is model structure; fitting its parameters is training work.

For sparse identification, construct a library and check its width before making the SINDy model:

```python
from neuromancer.dynamics.library import PolynomialLibrary
from neuromancer.dynamics.ode import SINDy

library = PolynomialLibrary(n_features=2, max_degree=2)
sindy = SINDy(library, threshold=1e-2)
x = torch.randn(6, 2)
dx = sindy(x)
assert dx.shape == (6, 2)
assert library.evaluate(x).shape == (6, library.shape[0])
```

Use `PolynomialLibrary` for polynomial candidates and `FourierLibrary` for bounded oscillatory candidates. The library functions should operate on two-dimensional tensors and preserve the input device/dtype if the workflow leaves CPU. Interpret `threshold` as a reporting/sparsification cutoff; it does not zero coefficients during every forward pass.

## 3. Compose networked physics into an ODE

Networked ODE construction has three separate objects: one agent per intrinsic contribution, one map from state names to column indices, and coupling modules carrying their pins.

```python
import torch
from neuromancer.dynamics import ode, physics

agents = [physics.RCNode(state_names=['T']),
          physics.SourceSink(state_names=['T'])]
state_map = physics.map_from_agents(agents)
coupling = physics.DeltaTemp(feature_name='T', symmetric=True, pins=[[0, 1]])
network = ode.GeneralNetworkedODE(
    map=state_map, agents=agents, couplings=[coupling],
    insize=2, outsize=2, inductive_bias='additive')
x = torch.randn(5, 2)
dx = network(x)
assert dx.shape == (5, 2)
```

For multiple features or exogenous signals, make each `state_names` list and `map` agree with the columns in `torch.cat([x, *args], dim=-1)`. `pins` refer to agent indices, not raw tensor columns. Use `symmetric=True` only when the interaction should add the opposite contribution to the receiving agent. `inductive_bias='general'` is not implemented; choose `additive` or `compositional` explicitly.

Keep coupling generation deterministic and inspect `map_from_agents` before connecting edges. A networked ODE can then be passed to `Euler`/`RK4` using the same `[B, nx]` plus optional-argument contract.

## 4. Compose a DAE with operator splitting

The package examples implement a neural DAE as sequential updates rather than expecting a generic DAE solver:

1. **Algebraic update:** a module receives the current state and control, computes algebraic quantities, and returns a complete state tensor with algebraic coordinates replaced.
2. **Differential update:** an `ODESystem` or RHS uses that complete state, writes derivatives for differential coordinates, and returns a fixed-width derivative tensor (zero or explicitly defined for algebraic coordinates).
3. **Integrator:** wrap the differential module in `RK4` or another stepper.
4. **Composition:** put the algebraic node before the ODE node in a graph/system.

A minimal algebraic-update pattern is:

```python
class AlgebraUpdate(torch.nn.Module):
    def forward(self, x, u):
        # x: [B, nx], u: [B, nu]
        z = x.clone()
        share = torch.sigmoid(torch.cat([x[:, :1], u[:, :1]], dim=-1)[:, :1])
        z[:, 2:3] = u[:, :1] * share
        z[:, 3:4] = u[:, :1] * (1.0 - share)
        return z
```

Ensure every update preserves `[B, nx]` and never silently drops the algebraic coordinates required by the next stage. Data acquisition and the long manifold-training example are deliberately outside this runtime recipe.

## 5. Build a PINN residual without detaching coordinates

The essential PINN pattern is a network over coordinate columns and an autograd residual. Use a single differentiable coordinate tensor or differentiable leaves for each coordinate:

```python
import torch
from neuromancer.modules.blocks import MLP

net = MLP(2, 1, linear_map=torch.nn.Linear,
          nonlin=torch.nn.Tanh, hsizes=[16, 16])
x = torch.linspace(-1, 1, 12).reshape(-1, 1).requires_grad_(True)
t = torch.linspace(0, 1, 12).reshape(-1, 1).requires_grad_(True)
y = net(x, t)                     # [12, 1]
one = torch.ones_like(y)
dy_dx, dy_dt = torch.autograd.grad(
    y, (x, t), grad_outputs=one,
    create_graph=True, retain_graph=True)
d2y_dx2 = torch.autograd.grad(
    dy_dx, x, grad_outputs=torch.ones_like(dy_dx),
    create_graph=True)[0]
residual = dy_dt - d2y_dx2         # [12, 1]
```

For a PDE with source terms, append the source to `residual`. For vector-valued outputs, compute component-specific gradients or use a Jacobian strategy; do not assume one summed gradient is the desired physical derivative. `create_graph=True` is required for second derivatives and for differentiating a residual into network parameters.

The symbolic alternative wraps the network in a `Node`, creates variables for the output and coordinates, then uses `.grad()` to form expressions such as `dy_dt - d2y_dx2`. That symbolic expression, `PenaltyLoss`, `Problem(grad_inference=True)`, and trainer configuration belong to `symbolic-problems`/`data-training`; this route owns the differentiable model and residual semantics. During evaluation, retain gradient-enabled coordinates whenever the residual is evaluated; do not put the residual forward under `torch.no_grad()`.

## 6. Use a FunctionEncoder for function families

A FunctionEncoder calibrates a basis representation from example input/output functions and evaluates it at query points. A safe small construction is:

```python
import torch
from neuromancer.modules.function_encoder import FunctionEncoder

basis = [torch.nn.Sequential(torch.nn.Linear(1, 8), torch.nn.Tanh(),
                             torch.nn.Linear(8, 1)) for _ in range(3)]
encoder = FunctionEncoder(basis, use_least_squares=True)
F, N, Q = 4, 10, 6
example_xs = torch.randn(F, N, 1)
example_ys = example_xs.square() + 0.2 * example_xs
query_xs = torch.randn(F, Q, 1)
representations, gram = encoder.compute_representation(example_xs, example_ys)
prediction = encoder.predict(query_xs, representations)
assert representations.shape == (F, 3)
assert gram.shape == (F, 3, 3)
assert prediction.shape == (F, Q, 1)
```

Use `use_least_squares=False` when the deterministic inner-product representation is wanted. Pass `lambd=...` to `compute_representation` for nonnegative Gram regularization in the least-squares path. An `average_function` subtracts an average prediction during calibration and adds it during prediction. Confirm that all basis modules return the same output width and that example/query function-batch axes are present; a single function's representation is rank 1 while a function batch's representation is rank 2.

The encoder is a model component only. It does not create an optimizer, dataset, trainer, callback, or loss. To fit basis parameters, hand the component to the training route; to use fixed basis modules, call it directly as above.

## 7. Interpolate exogenous inputs

Use offline interpolation when a fixed sampled signal is available:

```python
t = torch.arange(6, dtype=torch.float32).reshape(-1, 1)
u = torch.cat([t, t.square()], dim=1)
interp = LinInterp_Offline(t, u)
tq = torch.tensor([[0.5], [3.25]])
uq = interp(tq)
assert uq.shape == (2, 2)
```

Use online interpolation for a moving two-point window:

```python
interp = LinInterp_Online()
t = torch.tensor([[[0.0], [1.0]], [[2.0], [4.0]]])  # [B,2,1]
u = torch.tensor([[[0.0], [2.0]], [[3.0], [7.0]]])  # [B,2,1]
tq = torch.tensor([[[0.25], [0.25]], [[3.0], [3.0]]])
uq = interp(tq, t, u)
assert uq.shape == (2, 1)
```

Keep actual time units consistent with the integrator step `h`; interpolation uses values, not integer time indices. Ensure adjacent online times differ and maintain a consistent time axis when batching.

## 8. Optional SDE construction

Only enter this workflow after confirming TorchSDE is importable. An SDE class provides drift and diagonal diffusion:

```python
import torch
from neuromancer.dynamics.sde import SDECoxIngersollRand
from neuromancer.dynamics.integrators import BasicSDEIntegrator

sde = SDECoxIngersollRand()
x0 = torch.ones(4, 1)
ts = torch.linspace(0, 0.1, 3)
trajectory = BasicSDEIntegrator(sde).integrate(x0, ts)
assert trajectory.shape == (3, 4, 1)
```

This output is time-major `[T, B, nx]`, unlike the ordinary one-step integrators. TorchSDE method/type restrictions apply; `BasicSDEIntegrator` currently selects Euler. Latent SDEs add encoder context, latent initial distributions, and optional adjoint parameters and should be treated as an advanced model component, not a CPU smoke test.

## Model versus training boundary

This sub-skill owns:

- module selection, width and rank contracts;
- RHS/SSM/physics construction;
- one-step integration and interpolation;
- autograd residual construction;
- function-basis representation and prediction;
- bounded, deterministic shape checks.

Route these concerns elsewhere:

- symbolic variables, equality/inequality residuals, `PenaltyLoss`, `Problem`, and graph overwrite rules: `symbolic-problems`;
- datasets, sequence windows, batching, optimizers, trainers, checkpoints, and callbacks: `data-training`;
- rollout systems, PSL simulators, control policies, preview, and closed-loop behavior: `control-simulation`;
- structured-map registry, map-specific dimensions, and native extensions: `structured-operators`.

A model is ready for the next route only after a tiny forward/shape check succeeds on representative rank-2 tensors and any autograd residual is confirmed to retain its coordinate graph.
