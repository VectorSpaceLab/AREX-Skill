---
name: jax-examples
description: "Plan and troubleshoot JAX DPM-Solver and ScoreSDE example
  workflows, including API differences, device behavior, old dependency pins,
  and safe command construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# JAX Examples

Use this sub-skill when a user asks about the repository's JAX solver file or
its JAX ScoreSDE example integration.

## When To Read

Read this for tasks that mention:

- `dpm_solver_jax.py`, JAX `NoiseScheduleVP`, JAX `DPM_Solver`, `predict_x0`,
  JAX `solver_type="dpm_solver"`, `pmap`, JIT, TPU/GPU JAX devices, or Flax.
- `examples/score_sde_jax`, ScoreSDE JAX configs, `get_dpm_solver_sampler`,
  `n_jitted_steps`, or JAX CIFAR-10 DPM-Solver sampling commands.
- JAX compatibility issues involving `model_type="score"`, classifier-free
  guidance, dynamic thresholding, old `jax`/`jaxlib` pins, or CPU fallback.

## Workflow

1. If the task is direct JAX API use, first read the core
   [`../core-api/SKILL.md`](../core-api/SKILL.md) and
   [`../core-api/references/api-reference.md`](../core-api/references/api-reference.md).
2. For ScoreSDE JAX command planning, read
   [`references/score-sde-jax-workflows.md`](references/score-sde-jax-workflows.md).
3. For JAX-specific caveats and patches, read
   [`references/jax-api-differences.md`](references/jax-api-differences.md).
4. Use [`scripts/build_jax_scoresde_command.py`](scripts/build_jax_scoresde_command.py)
   to print a command template without launching a model run.
5. Use [`../core-api/scripts/minimal_jax_sample.py`](../core-api/scripts/minimal_jax_sample.py)
   or root [`../../scripts/check_dpm_solver_environment.py`](../../scripts/check_dpm_solver_environment.py)
   for tiny solver smoke tests before touching the full ScoreSDE stack.

## ScoreSDE JAX Command Pattern

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

The original JAX example wraps the sampler in `jax.pmap`, so real execution
expects a compatible JAX device setup and batch shapes divisible by local device
count.

## JAX-Specific Defaults

- Use `predict_x0=False` for the DPM-Solver/noise-prediction path.
- Use `predict_x0=True` for the DPM-Solver++/data-prediction path, but avoid
  `thresholding=True` until the thresholding caveat is patched and tested.
- Use `solver_type="dpm_solver"`, not PyTorch's `"dpmsolver"` spelling.
- Use `denoise=True` only when the extra NFE is acceptable.
- Use `config.training.n_jitted_steps` carefully: larger values can improve
  training speed but increase memory and must divide logging/checkpointing
  frequencies as documented by the example.

## Safety Notes

- The root JAX solver can be smoke-tested on CPU. That does not verify GPU/TPU
  acceleration or full ScoreSDE compatibility.
- Original JAX requirements pin very old `jax`, `jaxlib`, `flax`, TensorFlow,
  and TensorFlow Datasets versions. Use a separate environment for full native
  example reproduction.
- Do not run notebooks, checkpoint downloads, CIFAR/FFHQ/CelebA evaluations, or
  TPU/GPU jobs without explicit user approval.

## Troubleshooting

Read [`references/troubleshooting.md`](references/troubleshooting.md) for JAX
example runtime, pmap, dependency, and API caveats. Shared solver guidance lives
in root [`../../references/troubleshooting.md`](../../references/troubleshooting.md).
