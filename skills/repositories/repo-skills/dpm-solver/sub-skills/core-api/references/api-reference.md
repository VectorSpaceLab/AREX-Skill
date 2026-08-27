# Core API Reference

This reference gives direct integration details for the bundled PyTorch and JAX
solver files.

## Public Objects

| Object | PyTorch file | JAX file | Purpose |
| --- | --- | --- | --- |
| `NoiseScheduleVP` | yes | yes | Forward VP schedule wrapper with alpha/sigma/log-SNR methods. |
| `model_wrapper` | yes | yes | Converts model outputs and guidance modes to a continuous-time noise prediction function. |
| `DPM_Solver` | yes | yes | High-order sampling/inversion solver. |
| `interpolate_fn` | yes | yes | Differentiable piecewise-linear interpolation for discrete schedules. |
| `expand_dims` | yes | yes | Batch-first broadcasting helper. |
| `to_sparse_list` | no | yes | JAX helper for grouping singlestep order sequences. |

## PyTorch Signatures

```python
NoiseScheduleVP(schedule="discrete", betas=None, alphas_cumprod=None,
                continuous_beta_0=0.1, continuous_beta_1=20.0,
                dtype=torch.float32)

model_wrapper(model, noise_schedule, model_type="noise", model_kwargs={},
              guidance_type="uncond", condition=None,
              unconditional_condition=None, guidance_scale=1.0,
              classifier_fn=None, classifier_kwargs={})

DPM_Solver(model_fn, noise_schedule, algorithm_type="dpmsolver++",
           correcting_x0_fn=None, correcting_xt_fn=None,
           thresholding_max_val=1.0, dynamic_thresholding_ratio=0.995)
```

PyTorch `DPM_Solver.sample`:

```python
sample(x, steps=20, t_start=None, t_end=None, order=2,
       skip_type="time_uniform", method="multistep",
       lower_order_final=True, denoise_to_zero=False,
       solver_type="dpmsolver", atol=0.0078, rtol=0.05,
       return_intermediate=False)
```

Other useful PyTorch methods:

- `inverse(...)`: same primary sampling controls, but integrates from data time
  toward noise time for inversion/editing workflows.
- `add_noise(x, t, noise=None)`: computes `alpha_t * x + sigma_t * noise` and
  returns one or many noised versions depending on `t` shape.
- `get_time_steps(skip_type, t_T, t_0, N, device)`: inspect time grids without
  running a full sample.

## JAX Signatures

```python
NoiseScheduleVP(schedule="discrete", betas=None, alphas_cumprod=None,
                continuous_beta_0=0.1, continuous_beta_1=20.0)

model_wrapper(model, noise_schedule, model_type="noise", model_kwargs={},
              guidance_type="uncond", condition=None,
              unconditional_condition=None, guidance_scale=1.0,
              classifier_fn=None, classifier_kwargs={})

DPM_Solver(model_fn, noise_schedule, predict_x0=False,
           thresholding=False, max_val=1.0)
```

JAX `DPM_Solver.sample`:

```python
sample(x, steps=20, t_start=None, t_end=None, order=3,
       skip_type="time_uniform", method="singlestep", denoise=False,
       solver_type="dpm_solver", atol=0.0078, rtol=0.05)
```

JAX differs from PyTorch in several user-visible ways:

- `predict_x0=True` is the DPM-Solver++-style path instead of
  `algorithm_type="dpmsolver++"`.
- `solver_type` uses `"dpm_solver"` with an underscore, while PyTorch uses
  `"dpmsolver"`.
- The root JAX solver does not provide `inverse`, `add_noise`,
  `return_intermediate`, `correcting_xt_fn`, or `lower_order_final`.
- JAX `NoiseScheduleVP` supports `"cosine"`; root PyTorch supports only
  `"discrete"` and `"linear"`.

## Model Parameterization

`model_wrapper` normalizes model outputs to noise prediction:

| `model_type` | Meaning | Conversion |
| --- | --- | --- |
| `"noise"` | Model predicts epsilon/noise. | Return output directly. |
| `"x_start"` | Model predicts clean data `x0`. | Convert `(x_t - alpha_t*x0) / sigma_t`. |
| `"v"` | Model predicts velocity. | Convert `alpha_t*v + sigma_t*x_t`. |
| `"score"` | Model predicts score. | Convert `-sigma_t*score`; verified in PyTorch only because root JAX assertion rejects it. |

## Guidance Modes

| `guidance_type` | Model contract | Extra inputs |
| --- | --- | --- |
| `"uncond"` | `model(x, t_input, **model_kwargs)` | none |
| `"classifier"` | model as above plus `classifier_fn(x, t_input, condition, **classifier_kwargs)` | `condition`, `classifier_fn`, `guidance_scale` |
| `"classifier-free"` | `model(x, t_input, cond, **model_kwargs)` | `condition`, `unconditional_condition`, `guidance_scale` |

For PyTorch classifier guidance, `classifier_fn` must be differentiable with
respect to `x`. For JAX classifier guidance, `classifier_fn` is wrapped by
`jax.grad`.

## Return Values

- `sample(...)` returns the final tensor/array by default.
- PyTorch `sample(..., return_intermediate=True)` returns `(x_end,
  intermediates)` for `multistep`, `singlestep`, and `singlestep_fixed`; the
  adaptive method is explicitly excluded.
- JAX `sample` returns only `x_end`.
- Example ScoreSDE wrapper functions return `(samples, nfe)` after inverse
  scaling; direct `DPM_Solver.sample` does not return NFE separately.

## Minimal Validation Pattern

Use a zero model to isolate solver mechanics from model quality:

```python
ns = NoiseScheduleVP(schedule="linear")
solver = DPM_Solver(lambda x, t: zeros_like(x), ns, ...)
out = solver.sample(ones_like_x, steps=2, order=1, method="multistep")
assert out.shape == x.shape
```

This validates import, schedule construction, time-step generation, and a basic
update path. It does not validate real diffusion sample quality.
