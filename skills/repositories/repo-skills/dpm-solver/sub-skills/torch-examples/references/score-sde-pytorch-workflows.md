# ScoreSDE PyTorch Workflows

The PyTorch ScoreSDE example adapts Yang Song's score-based generative modeling
code and adds a DPM-Solver sampler option. Use this reference for command
planning and dependency/runtime expectations.

## Command Surface

The high-level entry point accepts:

```text
main.py --config <config.py> --mode <train|eval> --workdir <dir> [--eval_folder eval]
```

DPM-Solver settings are supplied through `ml_collections` command-line overrides
on the config object.

The DPM-Solver sampler factory signature in the example is:

```python
get_dpm_solver_sampler(
    sde,
    shape,
    inverse_scaler,
    steps=10,
    eps=1e-3,
    skip_type="logSNR",
    method="singlestep",
    order=3,
    denoise=False,
    algorithm_type="dpmsolver",
    thresholding=False,
    rtol=0.05,
    atol=0.0078,
    device="cuda",
)
```

It creates `NoiseScheduleVP("linear", continuous_beta_0=sde.beta_0,
continuous_beta_1=sde.beta_1)`, obtains a score/noise function from the ScoreSDE
model utilities, samples from the SDE prior, runs `DPM_Solver.sample`, and then
applies the inverse data scaler.

## CIFAR-10 Evaluation Pattern

The repository's sample shell uses a 10-step, order-3, `logSNR`, singlestep
configuration:

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

Before execution, confirm that the expected checkpoint and CIFAR-10 stats files
are available. Without them, this command may download, fail, or run expensive
work rather than serving as a quick smoke test.

## Training Versus Evaluation

- `--mode train` creates experiment directories, initializes a model, builds
  dataset iterators, logs TensorBoard summaries, and writes checkpoints. Treat
  it as a long-running training workflow.
- `--mode eval` can evaluate loss, generate samples, compute FID/KID/IS, or
  compute likelihood depending on config flags. Treat sample and likelihood
  evaluation as model/data/checkpoint-dependent.
- For simple DPM-Solver API verification, use the core API smoke scripts instead
  of running ScoreSDE.

## Dependency Notes

The original PyTorch ScoreSDE requirements include older TensorFlow evaluation
packages, TensorFlow Datasets, TensorFlow Probability, PyTorch, torchvision, and
`ninja`. They are not needed for the root solver smoke check but may be required
for full ScoreSDE metrics and model code.

Use an isolated environment for full ScoreSDE runs. Do not install these pins
into a shared environment unless the user accepts compatibility risk.

## Adapting To A Custom ScoreSDE Project

1. Use the model's SDE object to set `continuous_beta_0`, `continuous_beta_1`,
   `T`, and `eps` instead of copying defaults blindly.
2. Ensure the score/noise function returns noise prediction in the same shape as
   the sampled prior.
3. Choose `skip_type="logSNR"` for CIFAR-like low-resolution tasks and compare
   `time_uniform` only when evidence suggests high-resolution behavior.
4. Keep `denoise=True` optional because it adds one extra NFE.
5. Use `algorithm_type="dpmsolver++"` plus thresholding only for pixel-space
   guided data-prediction behavior that has been validated.
