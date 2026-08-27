# Dynamics modeling API and shape contracts

This reference describes the importable public modules used by the dynamics route. Prefer explicit submodule imports when code is intended to be stable across installations; the package also re-exports many of these names at its top level.

## Stable imports

```python
from neuromancer.modules.blocks import (
    Block, Linear, MLP, MLPDropout, MLP_bounds, ResMLP,
    InputConvexNN, PosDef, BasisLinear, Poly2, KANBlock,
    PytorchRNN, RNN,
)
from neuromancer.modules.activations import activations, SoftExponential, SmoothedReLU
from neuromancer.modules.functions import bounds_scaling, bounds_clamp, window_functions
from neuromancer.modules.function_encoder import FunctionEncoder
from neuromancer.modules.rnn import RNN as CoreRNN, RNNCell

from neuromancer.dynamics.ode import (
    SSM, ODESystem, GeneralNetworkedODE, SINDy,
    LorenzParam, LorenzControl, LotkaVolterraParam,
    LotkaVolterraHybrid, BrusselatorParam, BrusselatorHybrid,
    VanDerPolControl, DuffingParam, TwoTankParam, CSTR_Param,
)
from neuromancer.dynamics.integrators import (
    Euler, Euler_Trap, RK2, RK4, RK4_Trap, Luther,
    Runge_Kutta_Fehlberg, MultiStep_PredictorCorrector,
    LeapFrog, Yoshida4, DiffEqIntegrator,
    BasicSDEIntegrator, LatentSDEIntegrator,
)
from neuromancer.dynamics.interpolation import LinInterp_Offline, LinInterp_Online
from neuromancer.dynamics.library import FunctionLibrary, PolynomialLibrary, FourierLibrary
from neuromancer.dynamics.physics import (
    Agent, RCNode, SourceSink, Interaction, DeltaTemp,
    DeltaTempSwitch, HVACConnection, map_from_agents,
)
```

`neuromancer.modules.blocks.MLP` and `neuromancer.dynamics.ode.ODESystem` are the preferred anchors for ordinary neural model construction. Root-level re-exports exist, but explicit imports make the dependency clear.

## Blocks and feature dimensions

### `Block`, `Linear`, and `MLP`

`Block.forward(*inputs)` accepts one or more tensors. With one input it forwards that tensor; with multiple inputs it concatenates them along `dim=-1` before calling `block_eval`. The ordinary contract is:

- each input: `[B, d_i]`;
- concatenated input: `[B, sum(d_i)]`;
- output: `[B, outsize]`.

The installed `MLP` constructor is:

```python
MLP(insize, outsize, bias=True, linear_map=slim.Linear,
    nonlin=SoftExponential, hsizes=[64], linargs={})
```

Use explicit non-mutable values in new code, for example `hsizes=[32, 32]` and `linargs={}`. `hsizes=[]` gives a direct linear map followed by the final identity. The `nonlin` argument is a **constructor**: each hidden layer is created as `nonlin()`. It should preserve the hidden feature width. The final layer has identity activation.

For portable small examples, `linear_map=torch.nn.Linear` avoids selecting a structured map. The default `slim.Linear` exposes the same block contract and can accept map-specific `linargs`; select specialized maps only after checking the `structured-operators` route.

`Linear(insize, outsize, bias=True, linear_map=..., nonlin=None, hsizes=None, linargs={})` ignores `nonlin` and `hsizes`; they are present for interface compatibility. `MLPDropout` adds dropout modules. `Dropout(p=0.0, at_train=False, at_test=True)` is disabled during training by default and may be enabled for test-time/Monte-Carlo use with `set_model_dropout_mode`.

Representative shape checks:

```python
x1 = torch.randn(7, 2)
x2 = torch.randn(7, 3)
net = MLP(5, 4, linear_map=torch.nn.Linear, nonlin=torch.nn.Tanh,
          hsizes=[8])
y = net(x1, x2)                 # [7, 4]
assert y.shape == (7, 4)
```

### Other useful blocks

| Block | Input/output contract or restriction |
|---|---|
| `MLP_bounds` | Same as `MLP`; applies differentiable `sigmoid_scale` or `relu_clamp` bounds to the final output. `min` and `max` may be scalars or broadcastable tensors. |
| `ResMLP` | Same rank-2 contract; hidden sizes must all be equal. `skip` controls residual frequency. |
| `InputConvexNN` | Same rank-2 contract; hidden sizes must all be equal and the positive hidden maps enforce the ICNN parameterization. |
| `PosDef(g, max=None, eps=0.01, d=1.0)` | Wraps a scalar-output block `g`; returns a positive-definite-style `[B, 1]` value relative to `g(0)` plus a quadratic term. |
| `Poly2()` | `[B, D] -> [B, D + D(D+1)/2]`; concatenates the original features and the upper-triangular quadratic monomials. |
| `BasisLinear(insize, outsize, expand=Poly2())` | Expands first, then linearly maps the expanded width to `[B, outsize]`. |
| `BilinearTorch(insize, outsize)` | Evaluates `torch.nn.Bilinear(x, x)`; input and both bilinear arguments have width `insize`. |
| `KANBlock` | Rank-2 features; with one domain returns a normal KAN output. Multiple domains blend per-domain outputs using `window_functions`; only 1-D/2-D input domains are implemented, and 2-D `num_domains` must be a perfect square. |
| `StackedMLP` | Rank-2 input and output; blends a base MLP with successive linear/nonlinear multi-fidelity layers. |

`KAN`, `KANLinear`, `Transformer`, and `InteractionEmbeddingMLP` are available for specialized uses. Treat `Transformer` input as a batch-first sequence `[B, T, insize]` and ensure `insize` is divisible by `num_heads`; its output is `[B, T, outsize]`. The interaction embedding block is specialized and should be checked against its index/embedding requirements before use.

## Activations and function helpers

`neuromancer.modules.activations.activations` maps names such as `relu`, `tanh`, `gelu`, `softplus`, `softexp`, `blu`, `aplu`, `prelu`, `pelu`, and `smoothedrelu` to constructors. Standard `torch.nn` activations are the safest defaults. `SoftExponential(alpha=0.0, tune_alpha=True)` preserves input shape and learns its scalar `alpha` by default; `soft_exp(alpha, x)` is the functional form.

Useful elementwise/domain helpers:

```python
z = bounds_scaling(x, xmin, xmax, scaling=1.0)  # sigmoid range
z = bounds_clamp(x, xmin=None, xmax=None)        # differentiable ReLU clamp
w = window_functions(x, num_domains, delta=1.9)
```

`window_functions` normalizes windows across domains. Inputs are `[B, 1]` or `[B, 2]`; for two coordinates, `num_domains` must be a perfect square. The helper derives bounds from the current batch, so it is not a fixed global coordinate transform.

## Sequence/RNN contracts

There are two wrappers with the `Block` interface:

- `PytorchRNN(insize, outsize, hsizes=[10], ...)` accepts `[B, T, insize]` or a rank-2 tensor (treated as one-step), runs a PyTorch RNN, and returns a linear projection of the final hidden state: `[B, outsize]`.
- `RNN(insize, outsize, hsizes=[1], ...)` accepts `[B, T, insize]` or a rank-2 one-step tensor and returns `[B, outsize]`. All hidden sizes must be equal. It retains final hidden state in `init_states` for open-loop context; call `reset()` before an independent rollout.

The lower-level `neuromancer.modules.rnn.RNN` is different: it expects `[T, B, input_size]`, returns `(sequence, hidden)` with shapes `[T, B, hidden_size]` and `[L, B, hidden_size]`, and requires equal hidden sizes across layers.

## Discrete and continuous systems

### `SSM`

```python
SSM(fx, fu, nx, nu, fd=None, nd=0)
```

It implements `x_next = fx(x) + fu(u) + fd(d)` when the disturbance branch is present. Call it with `x: [B, nx]`, `u: [B, nu]`, and optional `d: [B, nd]`; output is `[B, nx]`. `in_features = nx + nu + nd`, `out_features = nx`. This is a discrete state transition, not an ODE RHS.

### `ODESystem`

```python
class MyRHS(ODESystem):
    def __init__(self, nx, nu=0):
        super().__init__(insize=nx + nu, outsize=nx)
        ...

    def ode_equations(self, x, u=None):
        ...
```

`ODESystem(insize, outsize)` stores `nx=outsize` and `nu=insize-outsize`. Its `forward` requires `x` rank 2 and calls `ode_equations(x, *args)`. An autonomous RHS is `[B, nx] -> [B, nx]`; a non-autonomous RHS is constructed with total `insize=nx+nu` but called as `rhs(x, u)`, not with a concatenated state/control tensor unless the implementation explicitly expects that.

Named systems follow this same convention. For example, `LorenzParam` and `BrusselatorParam` are autonomous; `VanDerPolControl(insize=3, outsize=2)` expects `x: [B, 2]` and `u: [B, 1]`; `LorenzControl(insize=5, outsize=3)` expects two control features; hybrid systems accept a block with the asserted input/output width and embed its result into known equations.

### `SINDy` and libraries

`FunctionLibrary(functions, n_features, function_names=None)` stores a list of callables over the columns of a rank-2 tensor. `evaluate(x)` returns `[B, n_terms]`; the current implementation allocates the result on CPU, so use CPU tensors for this path or audit device behavior before moving it.

- `PolynomialLibrary(n_features, max_degree=2)` includes a constant and all combinations with replacement up to the requested total degree.
- `FourierLibrary(n_features, max_freq=2, include_sin=True, include_cos=True)` creates sine/cosine candidates.
- `SINDy(library, threshold=1e-2)` requires a `FunctionLibrary`; it learns coefficient matrix shaped `library.shape`, evaluates `[B, n_features] -> [B, n_terms] @ [n_terms, n_features]`, and returns `[B, n_features]`. Its string form suppresses coefficients below `threshold`; the threshold is presentation/sparsity interpretation, not an automatic optimizer.

## Integrator families

All integrators wrap a callable `block` with `in_features` and `out_features`, expose `h`, and return one next-state tensor unless noted otherwise. The standard one-step contract is:

```text
x: [B, nx], optional args such as u: [B, nu]  ->  [B, nx]
```

- `Euler(block, h=1.0)`, `Euler_Trap`, `RK2`, `RK4`, `RK4_Trap`, `Luther`, and `Runge_Kutta_Fehlberg` are explicit/autonomous-or-argument-passing step methods. `RK4` is the usual robust default for a small differentiable stepper.
- `DiffEqIntegrator(block, h=0.001, method='euler')` calls `torchdiffeq.odeint_adjoint` over `[0, h]` and returns the final `[B, nx]` state. Supported method names in the wrapper include `dopri8`, `dopri5`, `bosh3`, `fehlberg2`, `adaptive_heun`, `euler`, `midpoint`, `rk4`, `explicit_adams`, `implicit_adams`, and `fixed_adams`. The wrapper does not expose `rtol`/`atol` in its constructor; do not assume arbitrary solver kwargs are accepted.
- `MultiStep_PredictorCorrector` expects a four-state history `[B, 4, nx]` and returns `[B, nx]`.
- `LeapFrog` and `Yoshida4` expect a second-order packed state `[B, 2*nx]` containing position then velocity and return the same shape.

The source integrator module imports both TorchDiffEq and TorchSDE at module import time. A target environment that omits either package may fail even when only deterministic Euler/RK4 is requested; see troubleshooting.

## SDE contracts

`BaseSDESystem` follows TorchSDE's interface: `f(t, y)` is drift and `g(t, y)` is diagonal diffusion, each returning `[B, state_size]`; classes set `noise_type='diagonal'` and `sde_type='ito'`.

- `BasicSDEIntegrator(block).integrate(x, t)` returns TorchSDE's time-major output `[T, B, state_size]` and currently fixes the method to Euler.
- `LatentSDEIntegrator(block, dt=1e-2, method='euler', adjoint=False)` returns `(zs, z0, log_ratio, xs, qz0_mean, qz0_logstd)`. With `adjoint=True`, the encoder must also be configured for adjoint integration.
- `StochasticLorenzAttractor`, `SDECoxIngersollRand`, `SDEOrnsteinUhlenbeck`, and `LotkaVolterraSDE` are small model anchors; the full latent encoder/decoder path has additional context, sequence, distribution, and TorchSDE requirements.

## Interpolation

`LinInterp_Offline(t, u)` stores fixed-sampling-rate series. `t` and `u` must both be rank 2, with `t: [T, 1]` ascending and `u: [T, nu]`. Calling it with `tq: [Q, 1]` returns `[Q, nu]`. Queries outside the stored range are linearly extrapolated using the first or last interval.

`LinInterp_Online()` is for a two-point moving window. Pass `t: [B, 2, 1]`, `u: [B, 2, nu]`, and `tq: [B, 2, 1]`; it uses the first query slice and returns `[B, nu]`. Time values must be in the same units and have a nonzero denominator.

## Physics and networked ODE composition

`Agent(state_names)` consumes a selected feature slice and returns an intrinsic contribution with the same width. `RCNode` scales its input by a positive capacitance floor; `SourceSink` returns zeros. `Interaction(feature_name, pins, symmetric)` consumes a two-agent feature pair `[B, 2]`; `DeltaTemp`, `DeltaTempSwitch`, and `HVACConnection` are provided interactions.

`map_from_agents(agents)` creates ordered feature maps. `GeneralNetworkedODE(map, agents, couplings, insize, outsize, inductive_bias='additive')` aggregates intrinsic and coupling physics. `additive` computes intrinsic plus coupling contributions; `compositional` feeds coupling contributions through intrinsic physics; `general` is explicitly not implemented. The returned derivative is truncated to the first `outsize` columns. Keep the map indices, `pins`, feature names, and `insize/outsize` consistent.

## FunctionEncoder

The installed constructor is:

```python
FunctionEncoder(basis_functions, average_function=None,
                use_least_squares=True)
```

`basis_functions` is either a list of modules or one module that evaluates all basis functions in parallel. For a list of `K` modules mapping `[*, D] -> [*, M]`:

- examples may be `[N, D]`/`[N, M]` for one function or `[F, N, D]`/`[F, N, M]` for `F` functions;
- `compute_representation(example_xs, example_ys)` returns `[K]` and a `[K, K]` Gram matrix for one function, or `[F, K]` and `[F, K, K]` for a function batch;
- `predict(query_xs, representations)` expects batched queries `[F, Q, D]` and returns `[F, Q, M]`;
- `predict_from_examples` computes the representation and predicts in one call;
- `average_function` enables residual representation, and `use_least_squares=False` selects the inner-product path.

The encoder has no built-in optimizer, trainer, data loader, or callback system. Put the encoder in a `Node` and hand it to the symbolic/data/training routes, or optimize it directly in application code. Keep example/query axes explicit; do not confuse `F` (function batch), `N` (calibration points), and `Q` (query points).
