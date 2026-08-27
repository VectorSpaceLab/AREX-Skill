# Core API Troubleshooting

## `NoiseScheduleVP` Errors

- **Unsupported schedule**: root PyTorch accepts `"discrete"` and `"linear"`;
  root JAX accepts `"discrete"`, `"linear"`, and `"cosine"`. If a PyTorch user
  needs cosine, either use the Stable Diffusion-derived solver copy as evidence
  for an adaptation or implement cosine support deliberately.
- **Missing `betas`/`alphas_cumprod`**: `schedule="discrete"` requires one of
  those arrays. `alphas_cumprod` is the DDPM cumulative product, while the
  solver's internal `alpha_t` is its square root.
- **Singular endpoint**: do not set `t_end=0`; use `1 / total_N` for discrete
  schedules or a small positive `eps` for continuous schedules.

## `model_wrapper` Errors

- **Wrong model arity**: unconditional models should accept `(x, t_input,
  **kwargs)`. Classifier-free models should accept `(x, t_input, cond,
  **kwargs)`.
- **Condition batch mismatch**: classifier-free guidance concatenates
  unconditional and conditional inputs. The two condition tensors must have
  compatible batch sizes and shapes.
- **Variance channels included**: if an improved-DDPM/guided-diffusion model
  returns `2*C` channels, strip the variance half before DPM-Solver sees it.
- **Wrong parameterization**: set `model_type` to the model's training target:
  `"noise"`, `"x_start"`, `"v"`, or PyTorch-only verified `"score"`.

## Solver Setting Errors

- **`steps < order` for multistep**: PyTorch and JAX multistep paths assert when
  the number of steps is smaller than the order. Lower the order or increase
  steps.
- **Wrong `solver_type` spelling**: PyTorch uses `"dpmsolver"`; JAX uses
  `"dpm_solver"`. Both also accept `"taylor"` for alternate update formulas.
- **Adaptive with intermediates**: PyTorch `return_intermediate=True` cannot be
  used with `method="adaptive"`.
- **Poor few-step quality**: try `lower_order_final=True` for PyTorch multistep
  with fewer than 10 steps, use order 2 for strong guidance, and verify the
  high-step DDIM baseline first.

## JAX Caveats To Surface Explicitly

- Root JAX `model_type="score"` is rejected by an assertion despite a conversion
  branch existing in the function body.
- Root JAX classifier-free guidance calls `.split(2)` on a JAX array and can
  fail on current JAX. Patch to `jnp.split` and test before relying on it.
- Root JAX thresholding can raise `TypeError: 'float' object is not iterable` on
  current JAX because it calls `jnp.max(s, max_val)`. Patch to an elementwise
  max and test before using.
- Original JAX example dependencies are old. A modern `jax`/`jaxlib` pair may
  import the root solver but still be incompatible with the old surrounding
  ScoreSDE/Flax code.

## Minimal Reproduction Template

Before debugging a real model, reduce to a zero model:

```python
ns = NoiseScheduleVP(schedule="linear")
solver = DPM_Solver(lambda x, t: zeros_like(x), ns, ...)
out = solver.sample(ones_like_x, steps=2, order=1, method="multistep")
assert out.shape == ones_like_x.shape
```

If this fails, the issue is backend installation or solver API usage. If it
passes, the issue is likely the host model wrapper, schedule, checkpoint, or
conditioning path.
