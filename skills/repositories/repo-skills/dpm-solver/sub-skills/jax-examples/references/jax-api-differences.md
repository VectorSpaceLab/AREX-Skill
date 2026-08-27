# JAX API Differences And Caveats

This page records differences between the root JAX solver and the root PyTorch
solver that affect user guidance.

## Naming Differences

| Concept | PyTorch | JAX |
| --- | --- | --- |
| DPM-Solver++ selection | `algorithm_type="dpmsolver++"` | `predict_x0=True` |
| DPM-Solver selection | `algorithm_type="dpmsolver"` | `predict_x0=False` |
| Solver type spelling | `solver_type="dpmsolver"` | `solver_type="dpm_solver"` |
| Final denoise argument | `denoise_to_zero=True` | `denoise=True` |
| Dynamic thresholding | `correcting_x0_fn="dynamic_thresholding"` | `thresholding=True` |
| Return intermediate samples | supported for non-adaptive methods | not exposed |
| Inversion helper | `inverse(...)` | not exposed |
| Add-noise helper | `add_noise(...)` | not exposed |

## Schedule Differences

The root JAX file supports `schedule="cosine"` in addition to `"discrete"` and
`"linear"`. It sets `T=0.9946` for cosine to avoid the singular endpoint. The
root PyTorch file supports only `"discrete"` and `"linear"`; a separate Stable
Diffusion-derived PyTorch copy in the source evidence includes cosine support,
but the bundled root PyTorch file remains faithful to the root implementation.

## Verified Compatibility Caveats

The following caveats were observed during live inspection with a current JAX
installation:

1. **`model_type="score"` is asserted away.** The body of `model_wrapper`
   contains a score-to-noise conversion branch, but the final assertion accepts
   only `"noise"`, `"x_start"`, and `"v"`. Do not recommend score-model JAX
   wrapping unless that assertion is patched and tested.
2. **Classifier-free guidance may fail.** The root JAX classifier-free branch
   calls `.split(2)` on a JAX array. Current JAX arrays do not expose that
   method. A likely patch is to use `jnp.split(noise_pred_fn(...), 2)`, followed
   by a tiny classifier-free guidance smoke test.
3. **Dynamic thresholding may fail.** `DPM_Solver(..., thresholding=True)` can
   raise `TypeError: 'float' object is not iterable` because the implementation
   calls `jnp.max(s, self.max_val)` instead of an elementwise maximum with
   correct broadcasting. Patch and test before relying on it.

## Safe Recommendation Pattern

For unpatched root JAX code, recommend:

```python
model_fn = model_wrapper(model, noise_schedule, model_type="noise", guidance_type="uncond")
solver = DPM_Solver(model_fn, noise_schedule, predict_x0=False)
out = solver.sample(x_T, steps=10, order=3, skip_type="logSNR", method="singlestep")
```

For guided JAX tasks, state the relevant caveat first and suggest verifying a
small patched function before launching a real ScoreSDE or Stable Diffusion run.

## Dependency Compatibility

The JAX ScoreSDE example requirements pin old versions:

```text
flax==0.3.1
jax==0.2.8
jaxlib==0.1.59
tensorflow==2.4.0
tensorflow_datasets==3.1.0
```

Those pins may not support modern Python versions or accelerator wheels. If a
user needs full native reproduction, create an isolated environment matching the
historical stack or port the surrounding ScoreSDE code to a modern JAX/Flax API
with focused tests.
