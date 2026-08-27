# Structured-operator API reference

This reference describes the public contracts needed for a CPU-oriented
NeuroMANCER 1.5.x workflow. It intentionally separates usable pure-Python
maps from the optional native butterfly implementation.

## Imports and registry

```python
import neuromancer.slim as slim
from neuromancer.modules.solvers import GradientProjection, IterativeSolver
from neuromancer.modules import lopo
```

`slim.__init__` re-exports the linear and recurrent symbols. The registry is a
mapping from the exact string key to a class, so a named selection is:

```python
Map = slim.maps["psd"]
layer = Map(insize=4, outsize=4, bias=False)
```

The release registry contains these keys (case and spelling are significant):

| Key | Class | Practical contract |
|---|---|---|
| `linear` | `Linear` | Torch-linear baseline; rectangular or square |
| `identity` | `IdentityLinear` | Identity initialization with gradients disabled; shape-compatible rectangular wrapper |
| `l0` | `L0Linear` | Stochastic input gates while training; supports `weight_decay`, `droprate_init`, `temperature`, and `lamda` |
| `nneg` | `NonNegativeLinear` | Effective weights are `relu(weight)` |
| `lasso` | `LassoLinear` | Difference of nonnegative parameters plus L1 `reg_error()` |
| `lstochastic` | `LeftStochasticLinear` | Softmax over dimension 0; effective columns sum to one |
| `rstochastic` | `RightStochasticLinear` | Softmax over dimension 1; effective rows sum to one |
| `pf` | `PerronFrobeniusLinear` | Nonnegative softmax map with row scaling bounded by `sigma_min`/`sigma_max` |
| `symmetric` | `SymmetricLinear` | Square; `(W + W.T) / 2` |
| `skew_symetric` | `SkewSymmetricLinear` | Square; intentionally retains the registry's `symetric` spelling |
| `damp_skew_symmetric` | `DampedSkewSymmetricLinear` | Square skew map plus learned diagonal damping |
| `split` | `SplitLinear` | `A = B - C`, with nonnegative `B` and `C` |
| `stable_split` | `StableSplitLinear` | Difference of Perron-Frobenius parameterizations |
| `spectral` | `SpectralLinear` | Householder factors and bounded singular values; `n_U_reflectors`, `n_V_reflectors`, `sigma_min`, `sigma_max` |
| `softSVD` | `SVDLinear` | Approximate `U Sigma V` parameterization with bounded singular values |
| `learnSVD` | `SVDLinearLearnBounds` | SVD map with learnable bounds; present, but the repository map test marks it as broken, so do not choose it by default |
| `orthogonal` | `OrthogonalLinear` | Square Householder reflections; use `bias=True` in this release |
| `psd` | `PSDLinear` | Square positive-semidefinite map, `W_eff = weight.T @ weight` |
| `symplectic` | `SymplecticLinear` | Even-dimensional construction |
| `butterfly` | `ButterflyLinear` | Optional native factor-backed path; excluded from the pure-Python smoke |
| `schur` | `SchurDecompositionLinear` | Square, and its implementation additionally requires an even size |
| `gershgorin` | `GershgorinLinear` | Square eigenvalue-disc parameterization |
| `bounded_Lp_norm` | `BoundedNormLinear` | Torch-linear map with norm bounds represented in `reg_error()` |
| `trivial_nullspace` | `TrivialNullSpaceLinear` | Tall map only: `insize <= outsize` and `bias=False` |
| `Power_bound` | `PowerBoundLinear` | Square power-method spectral-radius regularizer; registry capitalization is intentional |

The registry is a useful selector, not a promise that every key is equally
portable. The recommended CPU set for a first shape/autograd check is
`linear`, `identity`, `nneg`, `psd`, `spectral`, `softSVD`, `rstochastic`,
`split`, and `trivial_nullspace`. Do not include `butterfly` in that check.

## Common map interface

`LinearBase(insize, outsize, bias=False, provide_weights=True)` stores
`in_features` and `out_features`, exposes `effective_W()`, `reg_error()`, and
`eig()`, and computes `x @ effective_W()` (plus bias when enabled). The
matrix used by the base interface has shape `(insize, outsize)` and a normal
input has shape `(batch, insize)`. `Linear(insize, outsize, bias=False,
**kwargs)` wraps `torch.nn.Linear`; its internal Torch weight is transposed by
`effective_W()` to match the SLiM orientation.

For a selected layer, a minimal contract check is:

```python
x = torch.randn(8, insize, requires_grad=True)
y = layer(x)
assert y.shape == (8, outsize)
assert layer.effective_W().shape == (insize, outsize)
(y.square().mean() + layer.reg_error()).backward()
```

`reg_error()` is a map-specific regularization term and is not necessarily a
constraint certificate. Use the effective matrix to inspect the parameterized
operator; do not infer an exact property from the class name alone.

## Dimension and parameterization choices

- **Square maps.** `SquareLinear` asserts `insize == outsize`. This includes
  `psd`, `symmetric`, `skew_symetric`, `damp_skew_symmetric`, `orthogonal`,
  `symplectic`, `schur`, `gershgorin`, and `Power_bound`, plus the symmetric
  SVD/spectral variants.
- **PSD.** `PSDLinear` forms `weight.T @ weight`, so it is square and has no
  independent unconstrained effective matrix. It is a good pure-Python choice
  for a positive-semidefinite hidden transition.
- **Orthogonal.** `OrthogonalLinear` applies Householder reflections. Although
  its constructor default is `bias=False`, this version's `forward()` adds
  `self.bias` without checking for `None`; instantiate it with `bias=True` for
  a working forward, or select another square map when a bias-free operator is
  required.
- **Spectral and SVD.** `SpectralLinear` applies Householder factors around a
  diagonal singular-value map; `SVDLinear` stores `U`, `V`, and bounded
  singular-value parameters. They accept rectangular dimensions, but their
  spectral settings are parameterization bounds rather than a post-forward
  proof. `sigma_min` and `sigma_max` must be numerically sensible.
- **Stochastic.** `lstochastic` applies `softmax(weight, dim=0)` and
  `rstochastic` applies `softmax(weight, dim=1)`. The implementation does not
  assert square dimensions, even though stochastic-matrix terminology often
  assumes a square matrix; state the actual dimensions in a model contract.
- **Split.** `SplitLinear` builds two `NonNegativeLinear` maps and subtracts
  their effective matrices. `StableSplitLinear` uses Perron-Frobenius maps and
  accepts `sigma_min`/`sigma_max`.
- **Trivial null space.** `TrivialNullSpaceLinear(..., rank=None,
  epsilon=0.1)` rejects a bias and rejects `insize > outsize`. Use it for a
  tall map; it is not a generic workaround for a square-only map.
- **Other structural choices.** `nneg`, `lasso`, `l0`, `pf`, and
  `bounded_Lp_norm` are useful when the prior is nonnegativity, sparsity, or a
  soft norm/radius preference. `learnSVD`, butterfly, and specialized Schur,
  symplectic, or Gershgorin settings need a separate targeted test.

## Structured recurrent layers

`RNNCell(input_size, hidden_size, bias=False, nonlin=torch.nn.functional.gelu,
hidden_map=slim.Linear, input_map=slim.Linear, input_args={}, hidden_args={})`
computes:

```text
h_next = nonlin(hidden_map(hidden) + input_map(input))
```

`input` and `hidden` are `(batch, feature)`, `input_map` is generally
rectangular, and `hidden_map` must map `hidden_size` to `hidden_size` when a
square parametrization is selected.

`RNN(input_size, hidden_size=16, num_layers=1, cell_args={})` expects a
sequence `(seq_len, batch, input_size)` and returns
`(outputs, final_hidden)`, with shapes `(seq_len, batch, hidden_size)` and
`(num_layers, batch, hidden_size)`. `cell_args` is forwarded to every cell;
use `input_args` and `hidden_args` to pass map-specific kwargs. `reg_error()`
aggregates the cell map errors.

## Blocks integration

The blocks layer constructor is:

```python
neuromancer.modules.blocks.Linear(
    insize, outsize, bias=True, linear_map=slim.Linear,
    nonlin=None, hsizes=None, linargs={}
)
```

The MLP constructor is:

```python
MLP(insize, outsize, bias=True, linear_map=slim.Linear,
    nonlin=SoftExponential, hsizes=[64], linargs={})
```

`linear_map` is a class or compatible callable. `linargs` is passed to each
layer. For example, `linear_map=slim.maps["split"]` is suitable for a small
rectangular MLP, while `linear_map=slim.maps["psd"]` requires every adjacent
width in `[insize] + hsizes + [outsize]` to be identical. Structured maps are
not a replacement for choosing ordinary model architecture or data shapes.

## Differentiable projection and iterative solvers

Import these from `neuromancer.modules.solvers`:

```python
GradientProjection(
    constraints, input_keys, output_keys=[], decay=0.1,
    num_steps=1, step_size=0.01, energy_update=True, name=None
)

IterativeSolver(
    constraints, input_keys, output_keys=[], num_steps=1,
    step_size=1.0, name=None
)
```

Both consume a dictionary of tensors. The base solver accepts a string
`input_keys`, but the concrete implementations assign `self.input_keys` again;
pass lists in actual workflows so iteration cannot accidentally walk the
characters of a key. They require `len(input_keys) == len(output_keys)` when
output keys are supplied; otherwise they reuse the input keys.

- `GradientProjection` accepts inequality constraints whose comparator string
  is `lt` or `gt`. It concatenates each constraint's violation tensor, forms a
  mean absolute per-batch energy, differentiates that energy with respect to
  each input key, and applies `num_steps` updates with a decaying step size.
  It returns a copy of the input dictionary with updated output keys. The
  input tensors must participate in autograd.
- `IterativeSolver` is an equality-only Newton-style prototype. It requires
  comparator `eq`, uses a Jacobian through the legacy `functorch.jacfwd` path,
  and inverts the resulting Jacobian. Treat it as experimental: verify a
  small, well-conditioned case before putting it in a training graph.

Constraint objects created by NeuroMANCER expose three output keys:
`[name, name + "_value", name + "_violation"]`. Projection reads the third;
iterative solving reads the second. Expression/comparator construction itself
belongs to the symbolic route.

## Safe LOP module overview

`neuromancer.modules.lopo` contains pure-PyTorch differentiable operator
building blocks, but it is an advanced numerical path rather than a baseline
smoke:

```python
lopo.ProxObjectivePlusEqualityConstraint(
    f, F, metric=None, JF_fixed=False, Hf_fixed=False, gamma=2.0
)
lopo.ProxBoxConstraint(f_lower_bound, f_upper_bound)
lopo.DRSolver(f_obj=None, F_ineq=None, F_eq=None, x_dim=0,
              n_ineq=0, n_eq=0, JF_fixed=False, Hf_fixed=False,
              num_steps=3, metric=None, state_slack_bound=1000.0)
lopo.ADMMSolver(..., alpha=0.5)
lopo.ParaMetricDiagonal(n_dim, parm_dim, upper_bound, lower_bound,
                        scl_upper_bound=0.2, scl_lower_bound=0.05)
```

The proximal operator expects unbatched functions of `(x, parms)` and lifts
them with `torch.func.vmap`, `grad`, Jacobians, and Hessians. `DRSolver` and
`ADMMSolver` use a second-order objective approximation and first-order
constraint approximation, adding nonnegative slack variables for inequalities.
Use `ProxBoxConstraint` as the least ambitious isolated check; use the full
solvers only with a tiny CPU fixture, differentiable functions, compatible
batch dimensions, a positive-definite metric/Hessian, and a correctly ranked
constraint Jacobian. No data download or training run is required for this
route.
