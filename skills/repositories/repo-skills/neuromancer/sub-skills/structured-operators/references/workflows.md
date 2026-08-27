# Structured-operator workflows

These workflows are deliberately small and offline. They establish dimensions,
parameterization, and autograd before a map is inserted into a larger model.

## 1. Select and validate a named map

Use a requirement-to-map decision rather than iterating through every class:

| Requirement | First CPU choice | Dimension rule |
|---|---|---|
| Unconstrained baseline | `linear` | Any `insize`, `outsize` |
| Positive semidefinite square operator | `psd` | `insize == outsize` |
| Orthogonal square transition | `orthogonal` with `bias=True` | `insize == outsize`; this release has an unconditional bias add |
| Bounded singular values | `spectral` or `softSVD` | Rectangular is supported by the implementation; test the chosen bounds |
| Row/column simplex structure | `rstochastic` / `lstochastic` | Softmax dimension is the operative contract; do not assume a square assertion |
| Difference of nonnegative maps | `split` | Any dimensions accepted by its child maps |
| Tall injective-style map | `trivial_nullspace` | `insize <= outsize`, `bias=False` |

Then run one deterministic check:

```python
import torch
import neuromancer.slim as slim

torch.manual_seed(0)
insize, outsize = 3, 5
layer = slim.maps["split"](insize, outsize, bias=False)
x = torch.randn(4, insize, requires_grad=True)
y = layer(x)
assert y.shape == (4, outsize)
assert layer.effective_W().shape == (insize, outsize)
(y.square().mean() + layer.reg_error()).backward()
```

For a square choice, change both dimensions together and apply its constructor
requirements before instantiation. `scripts/maps_smoke.py --run` performs the
same kind of check for a small, intentionally selected pure-Python set.

Inspect `sorted(slim.maps)` when accepting a user-provided map name. Registry
keys are not normalized: `softSVD`, `Power_bound`, and the misspelled
`skew_symetric` must be used exactly as published. Do not treat the presence of
a registry key as verification of its optional backend or every keyword.

## 2. Use a structured RNN

The low-level RNN keeps the sequence-first convention used in its public
examples:

```python
import torch
import neuromancer.slim as slim

rnn = slim.RNN(
    input_size=3,
    hidden_size=4,
    num_layers=2,
    cell_args={
        "bias": True,
        "input_map": slim.Linear,
        "hidden_map": slim.PerronFrobeniusLinear,
        "hidden_args": {"sigma_min": 0.1, "sigma_max": 1.0},
    },
)
sequence = torch.randn(6, 8, 3)       # seq_len, batch, input_size
outputs, final_hidden = rnn(sequence)
assert outputs.shape == (6, 8, 4)
assert final_hidden.shape == (2, 8, 4)
```

Use a square map only for `hidden_map`, because it is constructed as
`hidden_size -> hidden_size`. The `input_map` maps `input_size -> hidden_size`
and can be ordinary `slim.Linear` or a compatible rectangular map. For custom
initial states, pass one state per layer with each state broadcastable to
`(batch, hidden_size)`; the built-in initial parameters have shape `(1,
hidden_size)` and broadcast over the batch.

`slim.RNNCell` is useful when the surrounding graph controls the recurrent
loop. Its forward call is `cell(input, hidden)`, and both tensors have a batch
axis. The cell's `reg_error()` averages its input and hidden map penalties;
`slim.RNN.reg_error()` averages over cells.

## 3. Put a map inside an MLP

`linear_map` is forwarded to every `Linear` block in the MLP, and `linargs` is
forwarded to every map constructor:

```python
import torch
from torch import nn
from neuromancer.modules.blocks import MLP
import neuromancer.slim as slim

model = MLP(
    insize=3,
    outsize=2,
    bias=False,
    linear_map=slim.maps["split"],
    nonlin=nn.Tanh,
    hsizes=[4],
)
y = model(torch.randn(5, 3))
assert y.shape == (5, 2)
```

To use a square map such as `psd`, select equal widths, for example
`MLP(4, 4, hsizes=[4], linear_map=slim.maps["psd"], bias=False)`. A mixed
`[3, 4, 2]` shape cannot use a square-only map. If the map needs parameters,
pass them through `linargs`, for example
`linargs={"sigma_min": 0.1, "sigma_max": 0.9}` for an appropriate spectral
map. Validate the whole layer chain, not only the first map.

This route covers the operator substitution. Ordinary activation, dynamics,
data, and training decisions remain with the neighboring modeling/training
routes.

## 4. Correct inequality violations with GradientProjection

Construct the symbolic constraint in the symbolic-problems route, then pass
the resulting constraint object to the solver:

```python
import torch
import neuromancer as nm
from neuromancer.modules.solvers import GradientProjection

x = nm.variable("x")
constraint = x < 0.0                 # comparator must be lt or gt
solver = GradientProjection(
    constraints=[constraint],
    input_keys=["x"],
    output_keys=["x_projected"],
    num_steps=2,
    step_size=0.1,
    decay=0.1,
)
state = {"x": torch.tensor([[1.0, -1.0]], requires_grad=True)}
updated = solver(state)
assert updated["x_projected"].shape == state["x"].shape
```

The solver computes an absolute violation energy per batch item and
backpropagates it through each `input_key`. Keep variables attached to the
computation graph. If there are multiple variables, supply matching input and
output key lists; every required symbolic input key must be present in the
state dictionary. `energy_update=False` changes which dictionary is used for
energy evaluation, so use the default until the update semantics are tested in
the surrounding graph.

The returned dictionary is a shallow copy and may retain keys created while a
symbolic constraint evaluates constants. Consumers should read the requested
output keys rather than assume the result contains only those keys.

## 5. Handle equality iteration conservatively

`IterativeSolver` is a Newton-style prototype for equality constraints only:

```python
from neuromancer.modules.solvers import IterativeSolver

solver = IterativeSolver(
    constraints=[equality_constraint],  # comparator string must be eq
    input_keys=["x"],
    output_keys=["x_new"],
    num_steps=1,
    step_size=1.0,
)
```

Its Jacobian path is based on the legacy `functorch.jacfwd` call in this
release, and the implementation assumes an invertible, well-conditioned
Jacobian. Start with a tiny scalar/vector fixture and inspect the first
forward before putting it in a training loop. A failed or ill-conditioned
Newton update is not repaired by increasing `num_steps`; check constraint
shape, differentiability, and conditioning first.

## 6. Use the LOP building blocks safely

For a first LOP check, use the box projection alone with unbatched bound
functions:

```python
import torch
from neuromancer.modules.lopo import ProxBoxConstraint

lower = lambda parms: -torch.ones(parms.shape[-1])
upper = lambda parms:  torch.ones(parms.shape[-1])
box = ProxBoxConstraint(lower, upper)
x = torch.tensor([[2.0, -0.5]])
parms = torch.zeros(1, 2)
y = box(x, parms)
assert y.shape == x.shape
assert torch.all(y <= 1.0) and torch.all(y >= -1.0)
```

`ProxObjectivePlusEqualityConstraint`, `DRSolver`, and `ADMMSolver` use
`torch.func` batching, gradients, Jacobians, Hessians, QR, triangular solves,
and sometimes Cholesky. Use functions of `(x, parms)` defined for one sample,
then check their batched output and Jacobian rank. Fixed-Jacobian or
fixed-Hessian modes are valid only when those quantities truly do not depend
on the iterated state. A tiny CPU fixture is the appropriate verification; no
benchmark, data acquisition, or model training is needed.

## 7. Verify the integration boundary

Before handing an operator to a larger NeuroMANCER graph, check all of the
following:

1. The last input axis equals `insize` and the last output axis equals
   `outsize`.
2. Every square or parity requirement is satisfied.
3. `effective_W()` and `reg_error()` execute on the selected device.
4. A representative scalar loss has a finite backward pass.
5. RNN sequence and hidden axes are explicit.
6. Solver dictionaries contain exact keys and constraints have the expected
   comparator type.
7. The chosen path does not silently select butterfly/native code or require
   downloads.
