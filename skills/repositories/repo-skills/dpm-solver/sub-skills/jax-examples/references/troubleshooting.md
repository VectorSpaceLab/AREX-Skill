# JAX Example Troubleshooting

## Import And Version Failures

- If `flax`, `tensorflow`, or `tensorflow_datasets` imports fail, distinguish
  full ScoreSDE example execution from root solver use. The root solver needs
  only JAX/JAXLIB for tiny smoke tests.
- The original requirements pin old JAX/Flax/TensorFlow versions. On modern
  Python, those exact pins may be unavailable. Use a historical environment or
  port the example deliberately.
- If JAX prints that a GPU may be present but CUDA-enabled `jaxlib` is missing,
  treat execution as CPU-only until the correct JAX accelerator package is
  installed and `jax.devices()` shows the expected accelerator.

## `pmap` And Shape Failures

- The ScoreSDE JAX sampler returns a `jax.pmap` function. Its leading dimensions
  must match `jax.local_device_count()`.
- Batch sizes should be divisible by local device count for full example runs.
- CPU-only `pmap` may behave differently from multi-GPU/TPU setups; use core
  smoke tests for API validation and reserve full runs for a prepared device
  environment.

## DPM-Solver Option Failures

- Use `solver_type="dpm_solver"`; PyTorch's `"dpmsolver"` spelling is not
  accepted by root JAX update functions.
- Use `steps >= order` for multistep methods.
- `denoise=True` adds final denoising and changes effective NFE.
- Avoid `thresholding=True` in unpatched root JAX code because of the verified
  `jnp.max` compatibility issue.

## Wrapper Caveats

- Do not recommend root JAX `model_type="score"` without a patch because the
  assertion rejects it.
- Do not recommend root JAX classifier-free guidance without a patch because the
  branch calls `.split(2)` on a JAX array.
- For classifier guidance, verify that `classifier_fn` returns a differentiable
  scalar or per-sample selected log-probability compatible with `jax.grad`.

## Asset And Runtime Failures

- ScoreSDE evaluation requires checkpoints, datasets, and FID stats for the
  selected config. Missing assets are not solver bugs.
- Large FID and likelihood evaluations are long-running and should be opt-in.
- `config.training.n_jitted_steps` trades memory for speed. If out-of-memory
  occurs, reduce it and ensure logging/checkpoint frequencies remain divisible
  by the new value.
