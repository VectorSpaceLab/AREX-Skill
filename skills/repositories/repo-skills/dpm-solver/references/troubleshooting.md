# Cross-Cutting Troubleshooting

Use this reference before diving into a workflow-specific troubleshooting page.
DPM-Solver failures usually come from a mismatch between solver assumptions and
the host diffusion model, not from the high-order update formulas alone.

## Import And Installation

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: dpm_solver_pytorch` or `dpm_solver_jax` | The repository has no installable root package; the solver is a copied single file. | Copy `scripts/dpm_solver_pytorch.py` or `scripts/dpm_solver_jax.py` into the user's project, or add the directory containing the copied file to `PYTHONPATH`. |
| `ModuleNotFoundError: torch` | PyTorch backend not installed. | Install a PyTorch build matching the target CPU/CUDA/ROCm environment, then run `python scripts/check_dpm_solver_environment.py --backend torch --smoke`. |
| `ModuleNotFoundError: jax` or `jaxlib` | JAX backend not installed. | Install `jax` and `jaxlib` for CPU use, or follow JAX's accelerator-specific install instructions before relying on GPU/TPU behavior. |
| Root example dependencies fail to resolve | Example folders pin older TensorFlow/JAX/Flax/PyTorch/Stable Diffusion dependency stacks. | Do not install every example requirement globally. Create a separate isolated environment for the exact example family, or use the distilled command builders for planning only. |

## Backend And Hardware

- CPU is enough for API inspection and tiny numerical smoke tests.
- Full image generation, FID evaluation, ScoreSDE checkpoints, guided-diffusion
  multi-GPU sampling, and Stable Diffusion usually need a GPU, substantial RAM,
  model weights, and data/stat files.
- A visible NVIDIA GPU is not proof that a specific framework build can use it.
  Probe `torch.cuda.is_available()` for PyTorch and `jax.devices()` for JAX.
- JAX may fall back to CPU if a CUDA-enabled `jaxlib` is absent. Treat that as
  an explicit limitation, not as accelerator verification.

## Noise Schedule Mismatch

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Samples diverge or are washed out | Wrong `betas`/`alphas_cumprod`, incorrect discrete-to-continuous mapping, or schedule mismatch with the trained model. | Build `NoiseScheduleVP(schedule="discrete", betas=...)` from the exact training beta schedule, or use `alphas_cumprod` from the host model when that is the canonical source. |
| `assert alphas_cumprod is not None` | `NoiseScheduleVP(schedule="discrete")` was constructed without `betas` or `alphas_cumprod`. | Pass one of them, not both unless the code path clearly ignores one. |
| Errors near `t=0` or `log(0)` | Time endpoint is too close to the singular endpoint. | Use default `t_end=1 / total_N` for discrete schedules or `eps` around `1e-3` for continuous SDEs with small step counts. |
| Low-resolution quality worsens with default spacing | High-resolution defaults were reused on CIFAR-like tasks. | Try `skip_type="logSNR"` and compare `steps=10,15,20`. |

## Model Wrapper Mismatch

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Shape mismatch in model output | The wrapped model does not return a tensor/array with the same shape as `x`. | Confirm the host model call signature and strip variance channels for improved-DDPM/guided-diffusion models that output both mean and variance. |
| Wrong conditioning behavior | `guidance_type`, `condition`, `unconditional_condition`, or `guidance_scale` does not match the model call contract. | For classifier-free guidance, verify the model accepts `model(x, t, cond, **kwargs)` and that conditional/unconditional batches align. |
| Classifier guidance gradients are zero or error | Classifier function does not return differentiable log probabilities for selected classes. | Make `classifier_fn(x, t, y)` return per-sample log probabilities or logits indexed by labels, and keep `x` differentiable for PyTorch autograd or JAX grad. |
| DPM-Solver++ with latent images looks clipped or poor | Dynamic thresholding was used on latent-space data. | Remove thresholding for Stable Diffusion or other unbounded latent-space models. |

## JAX-Specific Caveats

The root JAX file is useful but has several compatibility traps on current JAX:

- `model_wrapper` documents `model_type="score"` and contains a conversion
  branch, but the final assertion rejects `"score"`. Treat score-model support
  as unavailable unless patched and tested.
- The classifier-free guidance branch uses `.split(2)` on a JAX array. Current
  JAX arrays do not expose that method; patch to `jnp.split(array, 2)` before
  relying on classifier-free JAX guidance.
- `DPM_Solver(..., thresholding=True)` can raise a `TypeError` because the code
  calls `jnp.max(s, self.max_val)`. Patch to an elementwise maximum with correct
  broadcasting before recommending JAX dynamic thresholding.
- JAX ScoreSDE examples use older pinned versions in the original requirements.
  Modern JAX may require source-level compatibility fixes in the surrounding
  ScoreSDE code even when the root solver imports.

## Stable Diffusion And Checkpoints

- Stable Diffusion examples require model checkpoints and configs. Do not run
  generation commands until the user confirms they have weights and accepts
  license/safety/runtime constraints.
- Use EMA-only checkpoint expectations when following the original v1 inference
  config.
- The DPM-Solver adapter expects a latent diffusion model exposing
  `alphas_cumprod`, `betas`, `device`, `apply_model`, and conditioning helpers.
- If the user uses Hugging Face Diffusers directly, route to a Diffusers skill
  for `DPMSolverMultistepScheduler` rather than adapting this repository's
  latent-diffusion adapter.

## Sanity Checks

Run the bundled checker before deeper debugging:

```bash
python scripts/check_dpm_solver_environment.py --backend both --smoke
```

A passing smoke check proves only that the copied solver can construct a simple
schedule and integrate a zero model on tiny tensors. It does not prove image
quality, checkpoint compatibility, FID parity, or accelerator throughput.
