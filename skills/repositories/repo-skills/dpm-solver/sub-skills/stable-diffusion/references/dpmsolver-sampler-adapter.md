# DPMSolverSampler Adapter

This reference explains the bundled Stable Diffusion sampler adapter template.
It is for projects that already have a compatible latent diffusion model object.

## Expected Model Interface

The adapter expects a model object with:

- `model.alphas_cumprod`: cumulative alpha schedule for `NoiseScheduleVP`.
- `model.betas`: tensor used to identify the device in the original adapter.
- `model.device`: current model device.
- `model.apply_model(x, t, conditioning)`: predicts noise for latent `x` at
  diffusion time `t` with conditioning.
- Conditioning helpers outside the adapter, such as `get_learned_conditioning`,
  when building text-to-image scripts.

The adapter does not load checkpoints, configs, tokenizers, safety checkers, or
watermarking. Those belong to the host Stable Diffusion application.

## Sample Method Contract

The bundled template mirrors the original sampler surface:

```python
sample(
    S,
    batch_size,
    shape,
    conditioning=None,
    unconditional_guidance_scale=1.0,
    unconditional_conditioning=None,
    skip_type="time_uniform",
    method="multistep",
    order=2,
    lower_order_final=True,
    correcting_xt_fn=None,
    t_start=None,
    t_end=None,
    x_T=None,
    **kwargs,
)
```

It returns `(samples, intermediates)` where `samples` is the final latent tensor
on the model device and `intermediates` are DPM-Solver intermediate latents.

## Encode / Inversion Helpers

The original adapter exposes:

- `stochastic_encode(x0, encode_ratio, noise=None)`: add noise to a clean latent
  at a ratio-mapped time.
- `encode(S, x, encode_ratio, conditioning=None, ...)`: run the inverse solver
  from a data latent toward a noisier latent state and return intermediates.
- `ratio_to_time(ratio)`: map `[0, 1]` to `[1/N, 1]`.
- `time_discrete_to_continuous` and `time_continuous_to_discrete`: convert
  between original discrete labels and continuous solver time.

Use these for editing/inpainting workflows only after confirming the host model,
input image/mask preprocessing, prompt conditioning, and checkpoint state.

## Corrector Hooks

`correcting_xt_fn(xt, t, step)` can modify intermediate latents between solver
steps. Treat it as an advanced hook for editing or constrained generation. It
must preserve tensor shape and device and should be tested on a tiny latent
before real generation.

## Adapting Safely

1. Copy the bundled root PyTorch solver file and the sampler adapter into the
   host project.
2. Fix imports so the adapter imports `NoiseScheduleVP`, `model_wrapper`, and
   `DPM_Solver` from the local copied solver module.
3. Run a parser/import check without loading checkpoints if possible.
4. Run one tiny latent-shape smoke test using a toy model object before loading
   real Stable Diffusion weights.
5. Only then run text-to-image or edit workflows with user-approved assets.

## Known Bug In Original Adapter Utility

The original `time_to_ratio` helper divides by `(1 - total_N)` instead of the
more natural `(1 - 1/total_N)`. Avoid relying on that helper without testing the
round trip against `ratio_to_time` in the adapted project.
