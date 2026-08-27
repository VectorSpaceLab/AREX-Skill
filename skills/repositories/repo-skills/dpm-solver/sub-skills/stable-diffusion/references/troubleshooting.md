# Stable Diffusion Troubleshooting

## Checkpoint And Config Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `FileNotFoundError` for checkpoint | Stable Diffusion weights are not present at the expected path. | Ask the user for a checkpoint path and confirm license/access. Do not auto-download gated weights. |
| Config/model state mismatch | Checkpoint variant does not match inference config or EMA expectation. | Use the config that belongs to the checkpoint family and verify missing/unexpected keys before generation. |
| Safety checker or feature extractor downloads unexpectedly | Original script imports Hugging Face safety checker at module load. | Make network/model downloads opt-in or disable/replace that safety path in controlled offline use, while preserving safety requirements. |
| Watermark package missing | `invisible-watermark`/`imwatermark` dependency absent. | Install the optional package or disable watermarking deliberately if allowed by the project policy. |

## Sampler Adapter Failures

- **No `alphas_cumprod`**: the adapter requires the host model's cumulative alpha
  schedule. Use the schedule source used by the original model sampler.
- **Condition batch mismatch**: classifier-free guidance doubles the latent
  batch internally. Ensure conditional and unconditional conditioning tensors
  match `batch_size`.
- **Wrong device**: random starting latents, schedule tensors, and model outputs
  must be on the same device as the model.
- **Unexpected return shape**: `model.apply_model` must return a latent/noise
  tensor with the same shape as `x`.
- **Dynamic thresholding requested**: reject by default for Stable Diffusion
  latents; use DPM-Solver++ without dynamic thresholding.

## Memory And Runtime Failures

- Reduce `--n_samples`, image size (`--H`, `--W`), or precision before changing
  solver settings.
- `--precision autocast` can reduce memory on CUDA; CPU generation remains slow.
- 20-25 DPM-Solver steps reduce denoising steps but do not remove model-loading
  or VAE decoding cost.
- If CUDA is unavailable, use command planning and tiny solver smoke tests; do
  not treat CPU Stable Diffusion generation as a practical check.

## DiffEdit / Inpainting Failures

- Editing workflows require consistent image preprocessing, mask shape, latent
  shape, and prompt conditioning.
- `encode_ratio` should map to a continuous solver time through the adapter's
  `ratio_to_time`; test time conversion before using it in an editing pipeline.
- Corrector functions must preserve latent shape and not detach needed tensors.
- Notebook cells may assume relative assets and loaded global variables; convert
  the logic into a controlled script before automation.

## Diffusers Boundary

If the user has code like:

```python
from diffusers import DPMSolverMultistepScheduler
```

then use a Diffusers-specific skill. This sub-skill is for the original
latent-diffusion adapter from the DPM-Solver repository, not for maintaining the
Hugging Face Diffusers scheduler implementation.
