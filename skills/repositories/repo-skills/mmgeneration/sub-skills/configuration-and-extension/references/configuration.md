# Configuration and Extension Guide

## Purpose

Use this reference when editing MMGeneration configs, extending the registry, or validating the shape of a dataset/model/runtime customization.

## Config structure

MMGeneration uses MMCV config inheritance.
Common patterns:

- `_base_` points at shared dataset, model, runtime, and metric blocks.
- `_delete_=True` replaces inherited nested dicts instead of merging them.
- `custom_imports` loads custom modules before registry construction.
- `--cfg-options` allows command-line overrides for a final config.

Example pattern from the docs:

```python
_base_ = [
    '../_base_/datasets/ffhq_flip.py',
    '../_base_/models/stylegan/stylegan2_base.py',
    '../_base_/default_runtime.py',
    '../_base_/default_metrics.py'
]
```

## Dataset and pipeline patterns

### Unconditional models

- `UnconditionalImageDataset(imgs_root, pipeline)`
- Usually combined with `RepeatDataset` for static GANs.
- `GrowScaleImgDataset` is the dynamic-resolution option for PGGAN/StyleGANv1-style training.

### Translation models

- `PairedImageDataset` for paired images.
- `UnpairedImageDataset` for domain A/B folders.
- Pipelines typically load, resize, crop, normalize, and collect `img_a`/`img_b` keys.

### SinGAN and quick checks

- `SinGANDataset` expects a single image and scale settings.
- `QuickTestImageDataset(size=(H, W))` is useful for smoke tests or shape checks.

## Registry and extension patterns

### Models and modules

- `mmgen.models.MODELS` stores top-level generative models.
- `mmgen.models.MODULES` stores generators, discriminators, losses, and helper modules.
- `build_model(cfg)` and `build_module(cfg)` resolve registered names.

### Models and losses

- Add the class.
- Decorate it with the appropriate registry.
- Import it from the owning package `__init__.py`.
- Reference it in the config.

Loss modules may use `data_info` to map generated outputs into the loss inputs.
That is how losses like `DiscShiftLoss` and the DDPM losses can consume a model output dict without extra glue code.

### Optimizers and runtime hooks

- `build_optimizers(model, optimizer_cfg)` builds one or more optimizers.
- Hooks and runners are registered through the config's runtime blocks, not by manual loop editing.
- Useful runtime knobs include `lr_config`, `momentum_config`, `checkpoint_config`, `log_config`, `custom_hooks`, and `evaluation`.

## CLI helpers

- `scripts/print_config.py` prints the merged config and resolves `custom_imports`.

Recommended usage:

```bash
python scripts/print_config.py path/to/config.py \
    --cfg-options model.generator.out_size=256
```

## Validation habits

When you change a config:

1. Print the final config.
2. Check that all registry names resolve.
3. Check that the dataset keys match the pipeline collectors.
4. Confirm that runtime blocks are compatible with the chosen training or evaluation launcher.

## Useful evidence sources

- `docs/en/tutorials/config.md`
- `docs/en/tutorials/customize_dataset.md`
- `docs/en/tutorials/customize_models.md`
- `docs/en/tutorials/customize_losses.md`
- `docs/en/tutorials/customize_runtime.md`
- `tests/test_datasets/*`
- `tests/test_cores/test_optimizers.py`
- `tests/test_cores/test_scheduler.py`
- `tests/test_cores/test_ema_hooks.py`
- `tests/test_cores/test_visualization_hook.py`
