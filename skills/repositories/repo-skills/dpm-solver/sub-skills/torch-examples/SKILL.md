---
name: torch-examples
description: "Plan and troubleshoot PyTorch DPM-Solver example workflows for
  DDPM, guided-diffusion, and ScoreSDE without running heavyweight checkpoints
  by default."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyTorch Examples

Use this sub-skill when a user asks how to adapt the repository's PyTorch
example workflows: DDPM, improved-DDPM, classifier-guided diffusion, or
ScoreSDE PyTorch sampling/evaluation with DPM-Solver.

## When To Read

Read this for tasks that mention:

- `examples/ddpm_and_guided-diffusion`, `sample_type=dpmsolver++`,
  `--dpm_solver_order`, `--skip_type`, `--thresholding`, `--scale`, or FID
  sampling commands.
- ScoreSDE PyTorch configs, `sampling.method="dpm_solver"`,
  `get_dpm_solver_sampler`, CIFAR-10 `ddpmpp_deep_continuous`, or
  `configs/vp/cifar10_ddpmpp_deep_continuous.py`.
- PyTorch checkpoint/data/FID stats requirements for DPM-Solver examples.

## Workflow

1. Decide which PyTorch family owns the task:
   - DDPM / guided-diffusion commands: read
     [`references/ddpm-guided-workflows.md`](references/ddpm-guided-workflows.md).
   - ScoreSDE PyTorch sampling: read
     [`references/score-sde-pytorch-workflows.md`](references/score-sde-pytorch-workflows.md).
2. Use the root [`../../references/solver-choice-guide.md`](../../references/solver-choice-guide.md)
   to choose `steps`, `order`, `method`, and `skip_type`.
3. Build a safe command plan with
   [`scripts/build_torch_example_command.py`](scripts/build_torch_example_command.py)
   instead of copying a shell script with fixed GPU IDs or paths.
4. Validate DPM-Solver option combinations with
   [`scripts/validate_torch_options.py`](scripts/validate_torch_options.py)
   before launching a full run.
5. Only run real examples after the user confirms checkpoint/stat files,
   datasets, GPU availability, output directory, and expected duration.

## Common Command Families

DDPM / guided-diffusion CIFAR-10 style:

```bash
python main.py --config cifar10.yml --exp <workdir> --sample --fid \
  --timesteps 10 --eta 0 --ni --skip_type logSNR \
  --sample_type dpmsolver++ --dpm_solver_order 3 \
  --dpm_solver_method multistep --dpm_solver_type dpmsolver
```

Guided ImageNet-style large-guidance family:

```bash
python main.py --config imagenet256_guided.yml --exp <workdir> --sample --fid \
  --timesteps 20 --eta 0 --ni --skip_type time_uniform \
  --sample_type dpmsolver++ --dpm_solver_order 2 \
  --dpm_solver_method multistep --dpm_solver_type dpmsolver \
  --scale 8.0 --thresholding
```

ScoreSDE PyTorch CIFAR-10 DPM-Solver sampler family:

```bash
python main.py --config configs/vp/cifar10_ddpmpp_deep_continuous.py \
  --mode eval --workdir <workdir> \
  --config.sampling.eps=1e-3 \
  --config.sampling.method=dpm_solver \
  --config.sampling.steps=10 \
  --config.sampling.skip_type=logSNR \
  --config.sampling.dpm_solver_order=3 \
  --config.sampling.dpm_solver_method=singlestep \
  --config.eval.batch_size=1000
```

## Safety Notes

- Original sample commands assume external checkpoints and FID stats. Some
  checkpoint paths auto-download; others must be placed manually.
- The DDPM/guided example uses distributed PyTorch with NCCL and a port. Avoid
  launching it on CPU-only hosts or without explicit GPU selection.
- ScoreSDE PyTorch requirements include TensorFlow-related evaluation packages
  and can conflict with modern Python stacks. Prefer a separate environment for
  full example execution.
- FID and full sample generation are long-running and should not be used as a
  routine skill verification check.

## Troubleshooting

Use [`references/troubleshooting.md`](references/troubleshooting.md) for
PyTorch example-specific checkpoint, config, distributed launch, option, and FID
errors. Use the root [`../../references/troubleshooting.md`](../../references/troubleshooting.md)
for shared import/backend/schedule issues.
