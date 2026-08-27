# Stable Diffusion Workflows

The Stable Diffusion example in this repository integrates DPM-Solver into the
classic latent-diffusion sampling scripts. Use this page for command planning
and runtime constraints.

## Text-To-Image Command

The original text-to-image example adds `--dpm_solver` to the classic
`txt2img.py` command:

```bash
python scripts/txt2img.py \
  --prompt "a photograph of an astronaut riding a horse" \
  --dpm_solver \
  --ddim_steps 25
```

Important details:

- `--ddim_steps` is reused as the number of DPM-Solver steps when `--dpm_solver`
  is selected.
- Default guidance scale is `--scale 7.5`.
- Default image size is 512x512 with latent channels `C=4` and downsampling
  factor `f=8`.
- `--fixed_code` reuses the same starting latent across samples.
- `--from-file` reads prompt lines and batches them by `--n_samples`.
- `--skip_grid` and `--skip_save` control output image writing.

## Model Asset Requirements

The classic example expects a latent-diffusion config and checkpoint, commonly
under a model directory such as:

```text
models/ldm/stable-diffusion-v1/model.ckpt
configs/stable-diffusion/v1-inference.yaml
```

When adapting the workflow:

1. Confirm the checkpoint license and usage restrictions.
2. Confirm the model config matches the checkpoint and EMA expectation.
3. Prefer explicit user-provided checkpoint/config paths over implicit cache
   locations.
4. Make downloads opt-in; do not run downloader scripts automatically.

## DPM-Solver Settings In The Adapter

The adapter constructs:

```python
noise_schedule = NoiseScheduleVP("discrete", alphas_cumprod=model.alphas_cumprod)
model_fn = model_wrapper(
    lambda x, t, c: model.apply_model(x, t, c),
    noise_schedule,
    model_type="noise",
    guidance_type="classifier-free",
    condition=conditioning,
    unconditional_condition=unconditional_conditioning,
    guidance_scale=unconditional_guidance_scale,
)
solver = DPM_Solver(model_fn, noise_schedule, algorithm_type="dpmsolver++")
```

It then calls:

```python
solver.sample(
    img,
    steps=S,
    skip_type="time_uniform",
    method="multistep",
    order=2,
    lower_order_final=True,
    return_intermediate=True,
)
```

These defaults reflect large-guidance latent diffusion usage. Do not add dynamic
thresholding because Stable Diffusion operates in unbounded latent space.

## Image Editing / DiffEdit

The repository documents a DiffEdit-style workflow with DPM-Solver acceleration:

1. Invert an image to a latent/noisy sequence.
2. Estimate or apply an edit mask.
3. Sample/inpaint with a different prompt.
4. Use about 20 DPM-Solver steps for acceleration.

The notebook is not a safe automated command. Treat it as conceptual evidence
and adapt the `DPMSolverSampler.encode`, `stochastic_encode`, and sampling calls
only after the user provides model weights, images, masks/prompts, and runtime
approval.

## Diffusers Boundary

If the user is using Hugging Face Diffusers directly, prefer the Diffusers
scheduler APIs, e.g. `DPMSolverMultistepScheduler.from_config(...)`, rather than
porting this legacy latent-diffusion adapter. This skill is best for the
original repository's adapter pattern and source-derived solver files.
