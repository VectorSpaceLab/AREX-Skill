# Training and Distribution Workflows

## Purpose

Use this reference when you need to launch or explain a training job, choose a launcher, or reason about the repo's distributed training behavior.

## Main entry point

`tools/train.py` is the repo's primary training driver.
It accepts a config path plus optional overrides for work directory, resume checkpoint, launcher choice, seed, and config options.

Common pattern:

```bash
python tools/train.py CONFIG \
    --work-dir work_dirs/run_name \
    --resume-from path/to/latest.pth \
    --launcher pytorch
```

## Launcher wrappers

- `tools/dist_train.sh` — thin distributed launcher wrapper around `tools/train.py`.
- `tools/slurm_train.sh` — Slurm-based wrapper that sets job and GPU allocation flags.

These wrappers are useful as command-shape references even when you do not run the original repo checkout.

## Training flow

1. `tools/train.py` loads the config and applies `--cfg-options`.
2. The runner and data loaders are built from the config.
3. The model is built from `cfg.model`.
4. The training loop is passed to `mmgen.apis.train_model`.
5. Validation hooks are registered only when the config asks for them.

## Distributed behavior

MMGeneration has both static and dynamic distributed behaviors:

- `DynamicIterBasedRunner` supports the repo's dynamic GAN training pattern.
- `use_ddp_wrapper` and `find_unused_parameters` control the DDP wrapper path.
- Some configs use `apex_amp`, but that path is only supported with DDP training.

The key design point is that the training step may need different parameter subsets for discriminator and generator updates, so the distributed setup must match the model family.

## CPU training

The docs allow CPU training for debugging by disabling CUDA visibility.
Use this only for configuration and code-path validation; it is not the practical path for large or dynamic GAN training.

## Hooks commonly seen in training configs

- `ExponentialMovingAverageHook`
- `VisualizeUnconditionalSamples`
- `VisualizationHook`
- `PGGANFetchDataHook`
- checkpoint, log, and evaluation hooks

These hooks are often the difference between a bare config and a useful training run.

## Evidence sources

- `tools/train.py`
- `mmgen/apis/train.py`
- `mmgen/core/runners/dynamic_iterbased_runner.py`
- `mmgen/core/hooks/*`
- `docs/en/tutorials/customize_runtime.md`
- `docs/en/tutorials/ddp_train_gans.md`
- `tests/test_models/test_static_unconditional_gan.py`
- `tests/test_models/test_ddpm.py`
