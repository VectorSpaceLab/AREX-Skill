# DDPM And Guided-Diffusion PyTorch Workflows

The repository adapts DDPM, improved-DDPM, and guided-diffusion sampling to
DPM-Solver through a PyTorch example family. Use this reference to construct
commands and understand constraints without relying on the original shell script.

## Workflow Surface

The example command parser accepts these DPM-Solver-relevant options:

| Option | Meaning |
| --- | --- |
| `--sample_type` | `dpmsolver` or `dpmsolver++` selects DPM-Solver algorithm family. Other values route to DDIM/DDPM baselines. |
| `--skip_type` | For DPM-Solver, use `logSNR`, `time_uniform`, or `time_quadratic`. |
| `--timesteps` | Number of solver function evaluations/steps, often 10 or 20. |
| `--dpm_solver_order` | Solver order, usually 2 for large classifier guidance and 3 for unconditional/light guidance. |
| `--dpm_solver_method` | `adaptive`, `singlestep`, `multistep`, or `singlestep_fixed`. |
| `--dpm_solver_type` | PyTorch update formula spelling: `dpmsolver` or `taylor`. |
| `--dpm_solver_atol`, `--dpm_solver_rtol` | Tolerances for `method=adaptive`. |
| `--scale` | Classifier guidance scale for guided configs. |
| `--thresholding` | Enables dynamic thresholding for pixel-space guided sampling. |
| `--denoise` | Adds final denoising step, reducing DPM steps by one in the example call. |
| `--lower_order_final` | Uses lower-order final steps, useful for very small step counts. |

## Unconditional CIFAR-10 / ImageNet64 Pattern

Use the order-3 multistep or singlestep family with `logSNR` for low-resolution
examples:

```bash
python main.py \
  --config cifar10.yml \
  --exp experiments/cifar10/dpmsolverpp_multistep_order3_10_logSNR \
  --sample --fid --timesteps 10 --eta 0 --ni \
  --skip_type logSNR \
  --sample_type dpmsolver++ \
  --dpm_solver_order 3 \
  --dpm_solver_method multistep \
  --dpm_solver_type dpmsolver
```

For `imagenet64.yml`, keep the same DPM-Solver options but update the config and
workdir. Confirm the matching checkpoint and FID stats before execution.

## Classifier-Guided ImageNet Pattern

Large classifier guidance uses order-2 DPM-Solver++ with dynamic thresholding:

```bash
python main.py \
  --config imagenet256_guided.yml \
  --exp experiments/imagenet256_guided/dpmsolverpp_multistep_order2_20_time_uniform_scale8_thresholding \
  --sample --fid --timesteps 20 --eta 0 --ni \
  --skip_type time_uniform \
  --sample_type dpmsolver++ \
  --dpm_solver_order 2 \
  --dpm_solver_method multistep \
  --dpm_solver_type dpmsolver \
  --scale 8.0 --thresholding
```

This workflow is not a safe default check: it expects classifier and diffusion
checkpoints, ImageNet stats, GPU memory, and distributed PyTorch/NCCL readiness.

## Integration Details

The example's diffusion runner does three important things before calling the
solver:

1. It strips variance channels when an improved-DDPM/guided-diffusion model
   emits `2*C` output channels, because DPM-Solver uses the ODE mean/noise path.
2. It constructs `NoiseScheduleVP(schedule="discrete", betas=self.betas)` from
   the model's beta schedule.
3. It uses `model_wrapper(..., guidance_type="classifier")` when a classifier
   is present; otherwise it uses unconditional guidance.

Do not omit the variance-channel strip when adapting guided-diffusion models
with `out_channels == 2 * in_channels`.

## Checkpoint And FID Assets

The example README describes multiple config-specific asset requirements:

- CIFAR-10 can auto-download a DDPM checkpoint into a user cache but still needs
  FID stats for quantitative evaluation.
- CelebA, ImageNet64, LSUN bedroom, and guided ImageNet variants require manual
  checkpoint/stat placement.
- Guided ImageNet configs require both diffusion and classifier checkpoints.

When the user asks to run a command, first ask or check whether the named
checkpoint and FID stat files already exist, and make downloads opt-in.
