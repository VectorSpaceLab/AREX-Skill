# Distribution and transform troubleshooting

## Invalid support or parameter values

**Symptoms**

- `nan`, `inf`, or `-inf` from `log_prob`.
- Validation errors about constraints, positive parameters, simplex values, or Cholesky factors.

**Likely cause**

A constructor parameter violates `arg_constraints`, or the value being scored is outside `support`.

**Fix**

```python
from numpyro.distributions.distribution import validation_enabled
with validation_enabled(True):
    d = dist.Beta(2.0, 5.0, validate_args=True)
    assert d.support.check(value).all()
    assert jnp.isfinite(d.log_prob(value)).all()
```

For guide parameters, add a constraint to `numpyro.param` and route the SVI side to `../svi-autoguides/`.

## Shape mismatch in `log_prob`

**Symptoms**

- `log_prob` has an extra trailing dimension.
- A scalar log-density is returned where one value per observation was expected.
- Broadcasting errors happen before inference begins.

**Likely cause**

Batch and event dimensions were confused, or constructor parameters broadcast differently than expected.

**Fix**

1. Print `d.batch_shape`, `d.event_shape`, `value.shape`, and `d.log_prob(value).shape`.
2. Use `.to_event(k)` or `dist.Independent(d, k)` only for rightmost dimensions of one event.
3. Keep observation axes as batch dimensions and handle them with `plate` in `../modeling-primitives/`.
4. Use `expand` only for batch broadcasting; it does not create event dimensions.

## `to_event` or `Independent` errors

**Symptoms**

- Error like `reinterpreted_batch_ndims <= len(base_distribution.batch_shape)`.
- Transform/domain errors after adding `to_event`.

**Likely cause**

The base distribution does not have enough batch dimensions to reinterpret, or the transform expects a different event rank.

**Fix**

Construct or expand the base distribution first:

```python
base = dist.Normal(jnp.zeros(3), 1.0)
vector_event = base.to_event(1)
```

For matrix-event transforms, use a distribution with the correct vector or matrix event size.

## Transform domain/codomain mismatch

**Symptoms**

- Inverse transform fails.
- `log_abs_det_jacobian` shape is unexpected.
- A composed transform returns values outside the distribution support.

**Likely cause**

Transforms were composed in the wrong order, or event dimensions do not match between base distribution and transform.

**Fix**

- Use `biject_to(constraint)` when possible.
- Test `transform.inv(transform(x))` and finite `log_abs_det_jacobian` outside inference.
- For shape-changing transforms (`StickBreakingTransform`, Cholesky transforms), verify the input/output dimensions explicitly.

## NaN/inf during inference from a distribution issue

**Symptoms**

- MCMC reports invalid initial parameters or divergences immediately.
- SVI losses become NaN on the first steps.

**Likely cause**

The model uses invalid distribution parameters for some data or guide state.

**Fix**

1. Run a distribution-object support/log-prob check here.
2. Trace the model in `../modeling-primitives/` to locate which site has invalid parameters.
3. For MCMC, adjust priors, transforms, or initialization in `../mcmc-diagnostics/`.
4. For SVI, add guide constraints or change ELBO/guide in `../svi-autoguides/`.

## Dtype and x64 precision issues

**Symptoms**

- Numerical errors for heavy-tailed, covariance, ODE, or time-series models.
- Tests or examples require `JAX_ENABLE_X64=1`.

**Likely cause**

Default JAX float32 precision is not enough for the computation.

**Fix**

Call `numpyro.enable_x64()` or set `JAX_ENABLE_X64=1` before importing/running JAX-heavy code. Do this before arrays are created. Re-run a small distribution smoke after changing precision.

## Optional TFP/Funsor distribution wrappers missing

**Symptoms**

- Error says a sample site's `fn` is not a NumPyro distribution and mentions Funsor or TensorFlow Probability.
- Import errors for `tensorflow_probability` or `funsor`.

**Likely cause**

The model is trying to use optional distribution backends not installed in the environment.

**Fix**

Use core NumPyro distributions when possible. If the task explicitly needs TFP or Funsor, route to `../advanced-contrib/` for optional dependency and wrapper guidance.
