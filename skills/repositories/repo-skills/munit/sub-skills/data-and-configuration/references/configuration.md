# MUNIT Configuration Reference

## When To Read

Read this when creating, shrinking, reviewing, or debugging a MUNIT YAML file. MUNIT uses plain YAML dictionaries consumed directly by `utils.get_config` and the trainer/data-loader functions.

## Required Top-Level Areas

Every training config used by the original entrypoints should include these groups:

| Area | Keys | Notes |
| --- | --- | --- |
| Logging/snapshots | `image_save_iter`, `image_display_iter`, `display_size`, `snapshot_save_iter`, `log_iter` | `display_size` images are indexed directly from each train/test dataset before training starts. Keep it no larger than every split length. |
| Optimization | `max_iter`, `batch_size`, `weight_decay`, `beta1`, `beta2`, `init`, `lr`, `lr_policy`, `step_size`, `gamma` | `lr_policy` supports `constant` or `step`; `init` supports `gaussian`, `kaiming`, `xavier`, `orthogonal`, `default`. |
| Loss weights | `gan_w`, `recon_x_w`, `recon_x_cyc_w`, `vgg_w` plus trainer-specific keys | `vgg_w > 0` can trigger VGG model file creation/download/conversion in the legacy utility. |
| Model | `gen: {...}`, `dis: {...}`, `input_dim_a`, `input_dim_b` | Image channels are normally `3`; grayscale can use `1` but output helpers expand grayscale grids to three channels. |
| Data | either `data_root` or all list-mode folder/list keys | See `data-formats.md`. |

## MUNIT-Specific Keys

The bundled configs target the `MUNIT` trainer and include:

```yaml
gen:
  dim: 64
  mlp_dim: 256
  style_dim: 8
  activ: relu
  n_downsample: 2
  n_res: 4
  pad_type: reflect
recon_s_w: 1
recon_c_w: 1
```

`gen.style_dim` controls the random style tensor shape `[num_style, style_dim, 1, 1]` at inference and `[display_size, style_dim, 1, 1]` in the trainer's fixed sampling buffers. Changing it breaks checkpoint compatibility unless the model is retrained or converted deliberately.

## UNIT-Specific Keys

The `UNIT` trainer can be selected by `--trainer UNIT`, but the bundled MUNIT configs are not sufficient by themselves. A UNIT config needs KL weights:

```yaml
recon_kl_w: <positive weight>
recon_kl_cyc_w: <positive weight>
```

UNIT does not use MUNIT style encoders or `gen.style_dim` for multimodal sampling. Route architecture questions to `../model-internals/` before converting a MUNIT config to UNIT.

## Generator and Discriminator Values

Recognized values are enforced by source assertions:

- Padding: `reflect`, `replicate`, `zero`.
- Normalization: `bn`, `in`, `ln`, `adain`, `none`, `sn`.
- Activation: `relu`, `lrelu`, `prelu`, `selu`, `tanh`, `none`.
- GAN loss: `lsgan`, `nsgan`.

Common bundled values:

```yaml
dis:
  dim: 64
  norm: none
  activ: lrelu
  n_layer: 4
  gan_type: lsgan
  num_scales: 3
  pad_type: reflect
```

## Resize and Crop Keys

MUNIT supports either one shared resize key or separate per-domain keys:

- Shared: `new_size`.
- Per-domain: `new_size_a` and `new_size_b`.

Training loaders apply resize, random crop to `crop_image_height` x `crop_image_width`, normalization to `[-1, 1]`, and random horizontal flip. Test/display loaders use center-free resize/crop behavior from the repository helpers; make sure source images are large enough for the crop size.

## Safe Edit Patterns

For a bounded smoke config:

- Lower `max_iter`, `image_display_iter`, `image_save_iter`, `snapshot_save_iter`, and `log_iter`.
- Lower `display_size` to fit every tiny split.
- Use `num_workers: 0` when debugging a dataset on a constrained host.
- Keep the full required key set and trainer-specific keys.
- Keep `data_root` or list-mode paths relative to the user's checkout or make them absolute.

Do not set smoke values to bypass CUDA: the original training and inference scripts call `.cuda()` unconditionally.

## Validation Helper

Run:

```bash
python scripts/validate_munit_config.py --config /path/to/config.yaml --repo-root /path/to/user/munit-checkout
```

The helper parses YAML, checks required keys and supported values, validates folder/list path shapes when possible, and returns nonzero for blocking config errors.
