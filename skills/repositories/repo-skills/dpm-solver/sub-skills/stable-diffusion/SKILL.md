---
name: stable-diffusion
description: "Use DPM-Solver with latent Stable Diffusion workflows, including
  DPMSolverSampler adaptation, txt2img command planning, inversion/editing
  concepts, and checkpoint/backend troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Stable Diffusion

Use this sub-skill when a user asks how this repository accelerates latent
Stable Diffusion sampling with DPM-Solver or how to adapt the repository's
`DPMSolverSampler` pattern into another latent-diffusion codebase.

## When To Read

Read this for tasks that mention:

- `txt2img.py --dpm_solver`, Stable Diffusion with DPM-Solver, 20-25 step
  Stable Diffusion sampling, or the original latent-diffusion scripts.
- `DPMSolverSampler`, `stochastic_encode`, `encode`, inversion for DiffEdit,
  inpainting/editing, or `correcting_xt_fn` in a latent sampler.
- Stable Diffusion checkpoint/config placement, safety checker/watermarking,
  GPU memory, or model-license constraints in this example family.

## Workflow

1. Read [`references/stable-diffusion-workflows.md`](references/stable-diffusion-workflows.md)
   for command families, model asset requirements, and DPM-Solver settings.
2. Read [`references/dpmsolver-sampler-adapter.md`](references/dpmsolver-sampler-adapter.md)
   when adapting the sampler class to a latent-diffusion model object.
3. Use [`scripts/build_sd_dpm_command.py`](scripts/build_sd_dpm_command.py) to
   construct a command plan without launching image generation.
4. Use [`scripts/stable_diffusion_dpmsolver_sampler.py`](scripts/stable_diffusion_dpmsolver_sampler.py)
   as a bundled, self-contained adapter template when a project already has a
   compatible latent diffusion model object.
5. Route direct Hugging Face Diffusers scheduler questions to a Diffusers skill
   instead of translating everything through this legacy latent-diffusion
   adapter.

## Default Stable Diffusion Sampling Family

```bash
python scripts/txt2img.py \
  --prompt "a photograph of an astronaut riding a horse" \
  --dpm_solver \
  --ddim_steps 25 \
  --scale 7.5
```

The original example uses the same `--ddim_steps` argument name for the number
of DPM-Solver steps when `--dpm_solver` is selected.

## Sampler Defaults

The adapter builds a discrete schedule from the model's `alphas_cumprod`, wraps
`model.apply_model` with classifier-free guidance, and calls the PyTorch
DPM-Solver++ path:

```python
DPM_Solver(model_fn, noise_schedule, algorithm_type="dpmsolver++")
```

Recommended defaults:

- `skip_type="time_uniform"`
- `method="multistep"`
- `order=2`
- `lower_order_final=True`
- 20-25 steps for common text-to-image usage

Do not enable dynamic thresholding for Stable Diffusion latents.

## Safety Notes

- Stable Diffusion checkpoints may be gated, licensed, unsafe for some uses, or
  absent. Confirm asset availability and intended use before running.
- Real generation requires substantial GPU memory for classic latent-diffusion
  code. CPU execution is not a practical verification check.
- Safety checker and watermark dependencies can download models or require
  optional packages in the original script.
- DiffEdit/inpainting notebooks are evidence for workflows, not safe default
  commands.

## Troubleshooting

Read [`references/troubleshooting.md`](references/troubleshooting.md) for
Stable Diffusion-specific checkpoint, config, sampler, safety checker, memory,
DiffEdit, and command issues. Shared solver settings live in
[`../../references/solver-choice-guide.md`](../../references/solver-choice-guide.md).
