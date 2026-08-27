# ScoreSDE JAX Workflows

The JAX ScoreSDE example integrates DPM-Solver into a Flax/JAX implementation of
score-based generative modeling. Use this page to plan commands and map config
fields without running heavyweight native examples by default.

## Entry Point

The high-level command shape is:

```text
main.py --config <config.py> --workdir <dir> --mode <train|eval> [--eval_folder eval]
```

DPM-Solver choices are supplied with `ml_collections` config overrides.

## DPM-Solver Sampler Factory

The example's sampler factory has this structure:

```python
get_dpm_solver_sampler(
    sde,
    model,
    shape,
    inverse_scaler,
    steps=10,
    eps=1e-3,
    skip_type="logSNR",
    method="singlestep",
    order=3,
    denoise=False,
    predict_x0=False,
    thresholding=False,
    rtol=0.05,
    atol=0.0078,
)
```

It constructs a linear `NoiseScheduleVP` from the SDE beta range, builds a noise
prediction function from ScoreSDE model utilities and EMA parameters, samples
from the SDE prior, runs `DPM_Solver.sample`, inverse-scales the result, and
returns `(samples, steps)` under `jax.pmap`.

## CIFAR-10 Evaluation Pattern

```bash
python main.py \
  --config configs/vp/cifar10_ddpmpp_deep_continuous.py \
  --mode eval \
  --workdir experiments/cifar10_ddpmpp_deep_continuous_steps \
  --config.sampling.eps=1e-3 \
  --config.sampling.method=dpm_solver \
  --config.sampling.steps=10 \
  --config.sampling.skip_type=logSNR \
  --config.sampling.dpm_solver_order=3 \
  --config.sampling.dpm_solver_method=singlestep \
  --config.eval.batch_size=1000
```

This command is not a routine smoke test. It expects a compatible environment,
pretrained checkpoint, dataset/stat assets, and device memory.

## Config Fields That Matter

| Field | Role |
| --- | --- |
| `config.training.sde` | Selects VP, subVP, or VE behavior and sets default sampling epsilon. |
| `config.model.beta_min`, `config.model.beta_max` | Feed the linear VP schedule used by DPM-Solver. |
| `config.model.num_scales` | Sets the number of SDE/noise scales. |
| `config.sampling.method` | Must be `dpm_solver` to select this sampler. |
| `config.sampling.steps` | Number of DPM-Solver function evaluations. |
| `config.sampling.skip_type` | Commonly `logSNR` for CIFAR-like examples. |
| `config.sampling.dpm_solver_order` | Usually 3 for the example's unconditional sampling. |
| `config.sampling.dpm_solver_method` | `singlestep` in the sample shell; `multistep` is also available. |
| `config.training.n_jitted_steps` | JAX training throughput/memory trade-off; log frequency must be divisible by it. |

## Device And `pmap` Considerations

- The sampler is wrapped by `jax.pmap(axis_name="batch")`, so array leading
  dimensions must match local device count expectations.
- `jax.local_device_count()` affects per-device sampling shapes.
- A CPU-only JAX installation can run small smoke tests but may be too slow or
  shape-sensitive for full example evaluation.
- JAX may preallocate accelerator memory unless configured otherwise; the
  example sets `XLA_PYTHON_CLIENT_PREALLOCATE=false`.

## When To Use Core Smoke Instead

Use `../core-api/scripts/minimal_jax_sample.py` when the user only needs to know
whether the solver imports and basic update formulas run. Full ScoreSDE example
execution is appropriate only when the user has assets, hardware, and time for
model sampling or evaluation.
