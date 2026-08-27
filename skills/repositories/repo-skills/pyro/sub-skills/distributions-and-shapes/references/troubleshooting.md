# Troubleshooting Distribution And Shape Errors

Use this reference after the router identifies a Pyro distribution, support,
`log_prob`, plate, HMM, stable, mixture, matching, transform, or device problem.
Keep validation enabled while reproducing the smallest failing case.

```python
import pyro
pyro.enable_validation(True)
```

For a single suspect distribution, also pass `validate_args=True` to its
constructor.

## First Diagnostic: Print The Shape Contract

Before editing model structure, inspect the distribution and observed value:

```python
fn = ...  # the distribution passed to pyro.sample
value = ...  # observed or sampled tensor
print("batch_shape:", fn.batch_shape)
print("event_shape:", fn.event_shape)
print("expected value shape:", fn.batch_shape + fn.event_shape)
print("actual value shape:", tuple(value.shape))
print("log_prob shape:", tuple(fn.log_prob(value).shape))
```

Inside a Pyro model or inference loop:

```python
from pyro import poutine

tr = poutine.trace(model).get_trace(*args, **kwargs)
tr.compute_log_prob()
print(tr.format_shapes())
```

Then apply the invariant:

```python
sample.shape == sample_shape + fn.batch_shape + fn.event_shape
fn.log_prob(sample).shape == sample_shape + fn.batch_shape
```

## Error And Recovery Matrix

| Symptom | Likely cause | Recovery |
|---|---|---|
| `invalid log_prob shape` at a Pyro sample site | A non-event batch dimension is not declared by `pyro.plate`, or a datum dimension should be event. | Add the missing `with pyro.plate(..., dim=...)`, or use `.to_event(n)` on the rightmost dependent dimensions, or permute data so plate dims are left of event dims. |
| `Expected [...], actual [...]` in shape check | Plate sizes/dims do not match the `log_prob` batch shape. | Compare `trace.format_shapes()` with the intended plate layout; set explicit negative `dim` values for nested plates. |
| `dim collision` within a plate | Two plates use the same negative dimension. | Give each reusable/nested plate a unique `dim`, e.g. outer `dim=-2`, inner `dim=-1`. |
| `plate stack overflow` | More plate dimensions are used than the inference algorithm budget allows. | For enumeration/inference, increase `max_plate_nesting`; route detailed enumeration mechanics to the enumeration sub-skill. |
| `ValueError: Expected value argument ... to be within the support ...` | Observation/sample violates distribution support. | Check dtype/range; clamp or transform parameters only if statistically valid; choose a distribution with matching support. |
| Constructor error from `arg_constraints` | A parameter violates constraints such as positive scale/rate, simplex, unit interval, or lower-Cholesky. | Put learnable parameters behind `pyro.param(..., constraint=...)` or apply `transform_to(constraint)` to unconstrained tensors. |
| `components event_shape disagree` from `MaskedMixture` | Mixture components have different event ranks/shapes. | Convert scalar batches to the same event rank with `.to_event(n)`, or choose components with identical event shapes. |
| Zero-inflated constructor says exactly one of `gate`/`gate_logits` is required | Both or neither were specified. | Specify exactly one; prefer logits for unconstrained neural-network outputs. |
| Generic `ZeroInflatedDistribution expected empty base_dist.event_shape` | Base distribution is vector/matrix-valued. | Use scalar count base distributions, or model multivariate zero inflation explicitly outside `ZeroInflatedDistribution`. |
| HMM `duration, event_shape mismatch` | Passed `duration` conflicts with an already nontrivial time dimension in parameters. | Use `duration=T` only when homogeneous parameters have time size 1 or unknown duration; otherwise let time be inferred from parameter broadcast shape. |
| `LinearHMM.log_prob() is not implemented` | `LinearHMM` supports sampling but not scoring. | Use `GaussianHMM`, `GammaGaussianHMM`, or another scored likelihood for `log_prob`; route inference alternatives to SVI/MCMC/reparameterization sub-skills. |
| `OneOneMatching does not support batching` or `OneTwoMatching does not support batching` | Matching logits have extra batch dimensions. | Loop over independent matchings, vectorize outside the distribution, or implement a custom batched approximation. |
| SciPy import error from matching `.mode()` | Matching `.mode()` uses `scipy.optimize.linear_sum_assignment`. | Avoid `.mode()`, use exact enumeration only for tiny cases, or ask the user to install SciPy in the active environment. |
| Stable code is extremely slow | `Stable.log_prob()` uses numerical integration. | For inference, consider stable reparameterizers or likelihood-free objectives; route algorithm decisions to sibling inference sub-skills. |
| Stable mean/variance is NaN/Inf | Stable moments are mathematically undefined for some `stability`. | Expect `mean` NaN when `stability <= 1` and `variance` Inf when `stability < 2`; do not treat this as an implementation bug. |
| CUDA tensor/device mismatch | Parameters, observations, constants, or indices are split across CPU and CUDA. | Create constants with `device=value.device`; move all tensors for one distribution site to one device. CUDA is optional/unverified in the minimum runtime. |
| NaN or Inf loss/log_prob | Invalid support, extreme parameters, unstable transforms, under/overflow, or too-large learning rate. | Enable validation, inspect each site's finite `log_prob`, constrain parameters, lower LR, clamp only model-derived scales/rates to meaningful ranges. |

## Fixing Invalid Support Or Constraint Errors

### Continuous Positive Parameters

Bad pattern:

```python
scale = pyro.param("scale", torch.tensor(-1.0))
pyro.sample("x", dist.Normal(0.0, scale))
```

Good pattern:

```python
import pyro.distributions.constraints as constraints

scale = pyro.param("scale", torch.tensor(1.0), constraint=constraints.positive)
pyro.sample("x", dist.Normal(0.0, scale))
```

For neural-network outputs, transform unconstrained tensors:

```python
scale = torch.nn.functional.softplus(raw_scale) + 1e-6
rate = torch.nn.functional.softplus(raw_rate) + 1e-6
probs = logits.softmax(-1)  # for simplex-valued probabilities
```

Prefer distribution constructors that accept logits (`Bernoulli`, `Categorical`,
`OneHotCategorical`, `ZeroInflated*` gate logits, `NegativeBinomial` logits) when
working with unconstrained real network outputs.

### Count And Categorical Observations

- `Poisson`, `NegativeBinomial`, `ZeroInflatedPoisson`, and
  `ZeroInflatedNegativeBinomial` require nonnegative integer observations.
- `Categorical` observations are integer class indices in `[0, K-1]` and shape
  `batch_shape`, not one-hot vectors.
- `OneHotCategorical` observations are one-hot vectors with event shape `(K,)`.
- `Binomial(total_count=...)` observations must be integers between 0 and
  `total_count`.

Repair checklist:

```python
assert obs.dtype in (torch.long, torch.int64, torch.float32, torch.float64)
assert torch.isfinite(obs.float()).all()
# Counts: nonnegative and integral.
assert (obs >= 0).all()
assert ((obs.float() % 1) == 0).all()
# Class indices for Categorical:
assert obs.dtype == torch.long and 0 <= int(obs.min()) and int(obs.max()) < K
```

If the data are continuous but nonnegative, use a continuous positive
distribution (`LogNormal`, `Gamma`, `Weibull`) rather than a count distribution.

### Simplex And Correlation Supports

For simplex-valued tensors, ensure the rightmost event dimension sums to one and
entries are nonnegative. For correlation matrices, ensure a symmetric positive
definite matrix with diagonal one. Prefer `LKJCholesky` plus scale construction
when the next distribution is `MultivariateNormal`.

```python
L_corr = pyro.sample("L_corr", dist.LKJCholesky(dim, concentration=1.0))
scale = pyro.param("scale", torch.ones(dim), constraint=constraints.positive)
L_cov = scale.diag_embed() @ L_corr
```

## Fixing `log_prob` Shape Errors

Pyro's shape checker suggests three fixes. Choose one deliberately:

1. **Add a plate** when a dimension is conditionally independent.
2. **Use `.to_event(n)`** when a rightmost dimension is part of one dependent
   event.
3. **Permute data/parameters** when event dimensions are not rightmost.

### Common Bad/Good Pair: Vector Datum

Bad: `D` is a vector feature dimension but Pyro sees it as batch.

```python
with pyro.plate("data", N):
    pyro.sample("y", dist.Normal(loc, scale), obs=y)  # loc/y shape [N, D]
```

Good:

```python
with pyro.plate("data", N, dim=-1):
    pyro.sample("y", dist.Normal(loc, scale).to_event(1), obs=y)
```

Alternative if each feature is truly conditionally independent and should be
represented by a plate:

```python
with pyro.plate("data", N, dim=-2), pyro.plate("features", D, dim=-1):
    pyro.sample("y", dist.Normal(loc, scale), obs=y)
```

### Common Bad/Good Pair: Image Or Matrix Datum

Bad: a two-dimensional event is left as batch.

```python
with pyro.plate("data", N):
    pyro.sample("image", dist.Bernoulli(logits=logits), obs=images)  # [N, H, W]
```

Good when one image is one dependent event:

```python
with pyro.plate("data", N, dim=-1):
    pyro.sample("image", dist.Bernoulli(logits=logits).to_event(2), obs=images)
```

Good when pixels are conditionally independent:

```python
with pyro.plate("data", N, dim=-3), pyro.plate("rows", H, dim=-2), pyro.plate("cols", W, dim=-1):
    pyro.sample("image", dist.Bernoulli(logits=logits), obs=images)
```

## HMM Duration And Broadcast Mistakes

Pyro HMM distributions include time in `event_shape`. The most common mistake is
placing the time axis in a `plate` or creating parameters whose time dimensions
cannot broadcast.

### DiscreteHMM Checklist

- `initial_logits.shape[-1] == state_dim`.
- `transition_logits.shape[-2:] == (state_dim, state_dim)`.
- `observation_dist.batch_shape[-1] == state_dim`.
- The time dimension, if present, is the dimension immediately before
  `state_dim` in `transition_logits` and `observation_dist.batch_shape`.
- Data shape is `batch_shape + (duration,) + observation_dist.event_shape`.
- Do not wrap the time dimension in `pyro.plate`.

Recovery pattern:

```python
# Observations are y.shape == (B, T, D), state count S.
init = torch.zeros(B, S)
trans = torch.zeros(B, T, S, S)
obs_dist = dist.Normal(torch.zeros(B, T, S, D), torch.ones(B, T, S, D)).to_event(1)
hmm = dist.DiscreteHMM(init, trans, obs_dist)
assert hmm.batch_shape == (B,)
assert hmm.event_shape == (T, D)
assert hmm.log_prob(y).shape == (B,)
```

### GaussianHMM Checklist

- `initial_dist.event_shape == (hidden_dim,)`.
- `transition_matrix.shape[-2:] == (hidden_dim, hidden_dim)`.
- `transition_dist.event_shape == (hidden_dim,)`.
- `observation_matrix.shape[-2:] == (hidden_dim, obs_dim)`.
- `observation_dist.event_shape == (obs_dim,)`.
- Broadcast all left/time shapes using a common final time dimension.
- Pass `duration=T` for homogeneous parameter sampling; omit or match it for
  heterogeneously time-indexed parameters.

If `duration` conflicts, remove it and inspect the inferred `event_shape`. If
`event_shape[0] == 1` but you need to sample length `T`, pass `duration=T`.

## Zero-Inflated Count Problems

Symptoms and fixes:

- **Too many or too few zeros:** `gate` is the extra-zero probability. It is not
  the base distribution's probability of zero. Inspect both `gate` and
  `base_dist.log_prob(0)`.
- **`gate` outside `[0,1]`:** use `gate_logits` for unconstrained outputs or
  constrain a parameter with `constraints.unit_interval`.
- **Shape mismatch:** `rate`/`total_count`/`probs`/`logits` and `gate`/`gate_logits`
  broadcast to `batch_shape`; the observation must have that shape under the
  corresponding plates.
- **Vector count event desired:** generic zero-inflated distributions require a
  scalar-event base distribution. Model vector counts as a plated or `.to_event()`
  collection of scalar zero-inflated counts, depending on independence.

## Mixture Problems

### `MaskedMixture`

- `mask` must be a boolean tensor.
- `component0.event_shape` must equal `component1.event_shape`.
- `mask`, component0 batch shape, and component1 batch shape broadcast to a
  common `batch_shape`.
- Component validation is disabled internally because each sample is valid only
  under the selected component; the mixture support uses a masked constraint.

### `MixtureSameFamily`

- The mixture `Categorical` batch shape should match the component batch shape
  excluding the rightmost component axis.
- The rightmost component batch dimension indexes mixture components.
- Use `.to_event(n)` on component distributions before constructing the mixture
  if a component's vector/matrix dimensions are dependent event dimensions.

### Pathwise Mixtures

- `MixtureOfDiagNormals` does not support dimension `D = 1`; use a regular
  scalar mixture instead.
- `GaussianScaleMixture` does not support `D = 1` and does not support batched
  parameters.
- Pathwise mixture gradients can be numerically delicate in high dimensions;
  check finite samples and finite `log_prob` before training.

## Stable Distribution Numerical Problems

Stable distribution failures are often mathematical/numerical rather than shape
errors.

Checklist:

- `0 < stability <= 2`, `-1 <= skew <= 1`, `scale > 0`.
- Prefer default `coords="S0"` for continuity around `stability=1`.
- Expect `Stable.log_prob()` to be much slower than Normal/StudentT because it
  uses numerical integration.
- Expect `mean` to be NaN when `stability <= 1` and `variance` to be Inf when
  `stability < 2`.
- If gradients blow up, inspect values near `stability=1`, reduce learning rate,
  and consider a reparameterized inference workflow via the inference/effect
  handler sub-skills.
- SciPy is not required for Pyro's core `Stable` constructor/sample/log_prob, but
  Pyro's native stable tests compare against SciPy; do not treat absence of
  SciPy as a core runtime failure unless the user's workflow requires those
  comparisons.

## Matching Distribution Problems

- Values are integer assignments. A `OneOneMatching` value must have event shape
  `(N,)`, entries in `[0, N-1]`, and each destination exactly once.
- A `OneTwoMatching` value must have event shape `(2*N,)`, entries in
  `[0, N-1]`, and each destination exactly twice.
- Exact enumeration grows combinatorially. Use exact mode only for tiny `N`.
- `bp_iters` enables approximate `log_prob()`/partition function but sampling is
  not implemented for approximate mode.
- `.mode()` requires SciPy. If SciPy is not available, do not call `.mode()`;
  for tiny cases, enumerate support and score assignments directly.

## Transform And Flow Problems

- `transform_to(constraint)` maps unconstrained values to a constraint but may
  not be bijective for every constraint; `biject_to(constraint)` requires a
  bijection when available.
- Transform event dimensions must be compatible with the base distribution's
  event rank. Multivariate transforms such as coupling/spline/autoregressive
  flows generally require vector events (`base.to_event(1)`).
- Learnable Pyro transforms are `TransformModule`s. If reused outside ordinary
  Pyro model execution and optimized manually, call `TransformedDistribution`'s
  `clear_cache()` after each optimizer step.
- If transformed values violate support, inspect transform domain/codomain and
  event_dim; a scalar transform applied to a vector event may not be the intended
  multivariate transformation.

## NaN/Inf Recovery Checklist

1. Enable validation and reproduce one forward pass.
2. Trace the model and inspect each site's finite `log_prob`:

   ```python
   tr = poutine.trace(model).get_trace(*args, **kwargs)
   tr.compute_log_prob()
   for name, site in tr.nodes.items():
       if site.get("type") == "sample" and "log_prob" in site:
           lp = site["log_prob"]
           print(name, tuple(lp.shape), torch.isfinite(lp).all().item(),
                 float(lp.detach().nan_to_num().min()),
                 float(lp.detach().nan_to_num().max()))
   ```

3. Check constraints for every positive, unit-interval, simplex, Cholesky, or
   ordered parameter.
4. Check observations for support and missing values. Use masks or
   `NanMaskedNormal`/`NanMaskedMultivariateNormal` only when that likelihood is
   statistically appropriate.
5. Replace extreme scales/rates with constrained parameters and small positive
   lower bounds only if the model semantics allow it.
6. Reduce optimizer learning rate or initialize closer to valid values if the
   first step is finite but later steps diverge.

## CUDA Optionality And Device Errors

CUDA distribution behavior was classified as optional for the minimum skill
runtime. If a user asks for CUDA support in their active environment:

- Check `torch.cuda.is_available()` and the installed torch build before
  promising GPU execution.
- Put all tensors in a distribution site on the same device:

  ```python
  options = dict(dtype=y.dtype, device=y.device)
  loc = torch.zeros(y.shape[-1], **options)
  scale = torch.ones(y.shape[-1], **options)
  idx = torch.arange(y.shape[-1], device=y.device)
  ```

- Avoid CPU defaults in HMM/matching/indexing code; `torch.arange`, `torch.eye`,
  and scalar tensors should specify device when combined with CUDA tensors.
- A CPU-only shape fix is still valid for distribution algebra; it is not proof
  that CUDA kernels or device-transfer behavior are verified.

## When To Reroute

- If the fix requires choosing SVI vs MCMC, an ELBO, an autoguide, or stable
  reparameterization strategy, route to `../svi-and-autoguides/` or
  `../mcmc-and-prediction/`.
- If the error mentions enumeration dims, `TraceEnum_ELBO`, `infer_discrete`,
  `config_enumerate`, or poutine handler order, route to
  `../effect-handlers-and-enumeration/` after recording the distribution shape
  facts.
- If the task is about domain examples, funsor HMMs, Horovod/Lightning, Graphviz,
  torchvision, pandas, scanpy, or zuko, route to
  `../contrib-and-domain-workflows/` and keep optional-dependency caveats clear.
