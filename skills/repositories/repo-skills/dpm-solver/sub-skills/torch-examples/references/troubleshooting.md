# PyTorch Example Troubleshooting

## Command And Config Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `FileNotFoundError` for config | Command is not being run from an example directory or config path is wrong. | Use the bundled command builder to construct a plan, then run from a prepared copy of the example family or adapt paths deliberately. |
| `NotImplementedError` for sample type or skip type | DDIM/DDPM options were mixed with DPM-Solver options. | For DPM-Solver, use `--sample_type dpmsolver` or `dpmsolver++` and `--skip_type logSNR`, `time_uniform`, or `time_quadratic`. |
| `steps < order` assertion | Multistep solver needs at least as many steps as its order. | Increase `--timesteps` or lower `--dpm_solver_order`. |
| Output folder prompt blocks automation | Existing output directory and no non-interactive flag. | Use `--ni` for DDPM/guided example automation only after confirming overwrite behavior is acceptable. |

## Distributed PyTorch / GPU Failures

The DDPM/guided example uses `torch.multiprocessing.spawn` and initializes an
NCCL process group based on `torch.cuda.device_count()`.

- On a CPU-only host, do not launch the distributed example as a validation
  check. Use core smoke tests instead.
- If the NCCL port is busy, choose a different `--port` value.
- If only one GPU is available, ensure GPU visibility variables and batch sizes
  match the host.
- If CUDA imports but allocations fail, reduce batch size or run only a tiny
  direct solver smoke test.

## Checkpoint And Data Failures

- Guided ImageNet configs require both a diffusion checkpoint and a classifier
  checkpoint.
- FID computation requires matching stats files. Missing stats should be treated
  as an asset issue, not a solver failure.
- Some checkpoints are configured under user cache-like paths in the original
  example; replace them with explicit user-provided paths in production runs.
- Dataset downloads and stat downloads require network access and may be large.

## DPM-Solver Option Pitfalls

- Use `--dpm_solver_type dpmsolver` for the PyTorch implementation spelling.
- Use `--thresholding` for pixel-space guided sampling with high guidance scale,
  but not for latent Stable Diffusion.
- For low-resolution CIFAR-style examples, `--skip_type logSNR` is a documented
  default. For high-resolution guided examples, use `time_uniform`.
- `--denoise` adds a final denoising operation and changes the effective number
  of solver steps in the example code.
- Improved-DDPM and guided-diffusion models may emit variance channels; ensure
  only the mean/noise half is passed to DPM-Solver.

## ScoreSDE PyTorch Dependency Failures

The ScoreSDE PyTorch example combines PyTorch, TensorFlow evaluation tooling,
TensorFlow Datasets, TensorFlow Probability, and optional CUDA extensions. If
installation fails:

1. Separate root solver smoke checks from full ScoreSDE example execution.
2. Use a fresh environment for the ScoreSDE example pins.
3. Decide whether the task truly needs FID/IS/KID evaluation or only command
   planning.
4. Treat fused CUDA extension compilation failures as optional performance or
   model-code issues unless the selected workflow explicitly requires them.
