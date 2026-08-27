# API Summary

This reference captures public API signatures and differences that were verified
from the bundled root solver modules. Use sub-skill references for longer
recipes.

## PyTorch Root Module

Import from the bundled file after copying it into a project or keeping the
skill `scripts/` directory on `PYTHONPATH`:

```python
from dpm_solver_pytorch import NoiseScheduleVP, model_wrapper, DPM_Solver
```

### `NoiseScheduleVP`

```python
NoiseScheduleVP(
    schedule="discrete",
    betas=None,
    alphas_cumprod=None,
    continuous_beta_0=0.1,
    continuous_beta_1=20.0,
    dtype=torch.float32,
)
```

Supported root PyTorch schedules are `"discrete"` and `"linear"`. For a
discrete-time model, pass exactly one of `betas` or `alphas_cumprod`. The
implementation stores `total_N`, `T`, time arrays for interpolation, and exposes
`marginal_log_mean_coeff(t)`, `marginal_alpha(t)`, `marginal_std(t)`,
`marginal_lambda(t)`, and `inverse_lambda(lambda_t)`.

### `model_wrapper`

```python
model_wrapper(
    model,
    noise_schedule,
    model_type="noise",
    model_kwargs={},
    guidance_type="uncond",
    condition=None,
    unconditional_condition=None,
    guidance_scale=1.0,
    classifier_fn=None,
    classifier_kwargs={},
)
```

`model_wrapper` converts a user model into a continuous-time noise-prediction
function. Root PyTorch supports `model_type` values `"noise"`, `"x_start"`,
`"v"`, and `"score"`, and guidance values `"uncond"`, `"classifier"`, and
`"classifier-free"`.

Model call contracts:

- Unconditional: `model(x, t_input, **model_kwargs)`.
- Classifier guidance: same model plus `classifier_fn(x, t_input, condition,
  **classifier_kwargs)` returning class logits or selected log probabilities.
- Classifier-free guidance: `model(x, t_input, cond, **model_kwargs)` and both
  `condition` plus `unconditional_condition` tensors.

### `DPM_Solver`

```python
DPM_Solver(
    model_fn,
    noise_schedule,
    algorithm_type="dpmsolver++",
    correcting_x0_fn=None,
    correcting_xt_fn=None,
    thresholding_max_val=1.0,
    dynamic_thresholding_ratio=0.995,
)
```

Important methods:

```python
sample(
    x,
    steps=20,
    t_start=None,
    t_end=None,
    order=2,
    skip_type="time_uniform",
    method="multistep",
    lower_order_final=True,
    denoise_to_zero=False,
    solver_type="dpmsolver",
    atol=0.0078,
    rtol=0.05,
    return_intermediate=False,
)

inverse(...same main sampling arguments...)
add_noise(x, t, noise=None)
```

`algorithm_type="dpmsolver++"` makes `DPM_Solver.model_fn` return data
prediction internally; `"dpmsolver"` keeps noise prediction. `return_intermediate=True`
returns `(x_end, intermediates)` for non-adaptive methods.

## JAX Root Module

Import from the bundled file after copying it into a project or keeping the
skill `scripts/` directory on `PYTHONPATH`:

```python
from dpm_solver_jax import NoiseScheduleVP, model_wrapper, DPM_Solver
```

### JAX `NoiseScheduleVP`

```python
NoiseScheduleVP(
    schedule="discrete",
    betas=None,
    alphas_cumprod=None,
    continuous_beta_0=0.1,
    continuous_beta_1=20.0,
)
```

JAX supports `"discrete"`, `"linear"`, and `"cosine"` schedules. For cosine,
`T` is set to `0.9946` to avoid the singular endpoint.

### JAX `model_wrapper`

```python
model_wrapper(
    model,
    noise_schedule,
    model_type="noise",
    model_kwargs={},
    guidance_type="uncond",
    condition=None,
    unconditional_condition=None,
    guidance_scale=1.0,
    classifier_fn=None,
    classifier_kwargs={},
)
```

The body contains a `"score"` conversion branch, but the final assertion in the
root JAX file only accepts `"noise"`, `"x_start"`, and `"v"`. Do not claim JAX
`model_type="score"` support unless the user has patched and tested that
assertion.

The inspected root JAX classifier-free path also calls `.split(2)` on a JAX
array, which fails on current JAX arrays. Prefer unconditional or classifier
guidance in the original root JAX file, or patch to use `jnp.split(..., 2)` with
a focused smoke test before relying on classifier-free JAX guidance.

### JAX `DPM_Solver`

```python
DPM_Solver(model_fn, noise_schedule, predict_x0=False, thresholding=False, max_val=1.0)
```

Important method:

```python
sample(
    x,
    steps=20,
    t_start=None,
    t_end=None,
    order=3,
    skip_type="time_uniform",
    method="singlestep",
    denoise=False,
    solver_type="dpm_solver",
    atol=0.0078,
    rtol=0.05,
)
```

`predict_x0=True` is the JAX counterpart to DPM-Solver++ data-prediction mode.
The JAX root solver does not expose PyTorch's `inverse`, `add_noise`,
`return_intermediate`, `correcting_xt_fn`, or `lower_order_final` controls.

The inspected root JAX dynamic thresholding path raises a `TypeError` on current
JAX because `jnp.max(s, self.max_val)` treats the second argument like an axis.
Do not recommend `thresholding=True` unless the user patches and verifies that
line, for example with `jnp.maximum(s, max_val)` and correct broadcasting.

## Shared Tensor Shape Rules

- Solver inputs are usually batch-first tensors/arrays.
- Time inputs inside sampling loops are scalar schedule values that get expanded
  for model calls as needed.
- User models must return tensors/arrays with the same sample shape as `x`.
- For classifier-free guidance, unconditional and conditional batches are
  concatenated, so condition tensors must have compatible batch dimensions.
- For image models, keep channel/order conventions from the host model: the
  root PyTorch examples use `NCHW`; JAX ScoreSDE examples use model-specific
  JAX layouts internally.

## Public Utility Functions

Both root modules expose:

- `interpolate_fn(x, xp, yp)`: differentiable piecewise-linear interpolation
  used for discrete schedules.
- `expand_dims(v, dims)`: expands a vector to batch-first broadcast shape.

The JAX module also exposes `to_sparse_list(l)`, used to group singlestep orders
for JAX loop execution.
