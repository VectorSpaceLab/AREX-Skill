# StyleGAN2/3 and ADA guide for StudioGAN

Use this guide when a config has `MODEL.backbone: stylegan2` or `MODEL.backbone: stylegan3`, or when enabling ADA/APA/DiffAug for limited-data training.

## Minimal StyleGAN identity

| Field | StyleGAN2 | StyleGAN3 |
| --- | --- | --- |
| `MODEL.backbone` | `stylegan2` | `stylegan3` |
| `STYLEGAN.stylegan3_cfg` | `N/A` | `stylegan3-t` or `stylegan3-r` |
| Discriminator implementation | StyleGAN2 discriminator | StyleGAN2 discriminator |
| `MODEL.z_dim` | `512` | `512` |
| `MODEL.w_dim` | `512` | `512` |
| `MODEL.g_act_fn` / `MODEL.d_act_fn` | `Auto` / `Auto` | `Auto` / `Auto` |
| `MODEL.apply_g_sn` / `MODEL.apply_d_sn` | `False` / `False` | `False` / `False` |
| Typical adversarial loss | `logistic` | `logistic` |

Critical compatibility rules:

- `MODEL.g_cond_mtd: cAdaIN` is allowed only for StyleGAN2/3.
- `MODEL.d_cond_mtd: SPD` is allowed only for StyleGAN2/3.
- StyleGAN2/3 generator conditioning is only `W/O` or `cAdaIN`.
- StyleGAN2/3 do not support spectral normalization.
- `MODEL.g_act_fn` and `MODEL.d_act_fn` must be `Auto`.
- StyleGAN3-r requires `STYLEGAN.blur_init_sigma`; `10` is the canonical starting value.
- `STYLEGAN.d_epilogue_mbstd_group_size` must be no larger than per-GPU batch size.

## Conditional versus unconditional choices

| Goal | Generator conditioning | Discriminator conditioning | Notes |
| --- | --- | --- | --- |
| Unconditional StyleGAN | `MODEL.g_cond_mtd: W/O` | `MODEL.d_cond_mtd: W/O` | Use one class or ignore labels. |
| Conditional StyleGAN | `MODEL.g_cond_mtd: cAdaIN` | `MODEL.d_cond_mtd: SPD`, `PD`, `2C`, or `D2DCE` | `SPD` and `cAdaIN` are common in the catalog. |
| Projection-style conditional discriminator | `cAdaIN` or `W/O` | `PD`, `SPD`, `2C`, `D2DCE` | `STYLEGAN.cond_type` controls discriminator class embedding use for selected methods. |

Match `DATA.num_classes` to the dataset. Conditional StyleGAN with mismatched class counts can build but train the wrong label semantics.

## Optimizer and lazy regularization

StudioGAN adjusts Adam learning rates and betas for StyleGAN lazy regularization intervals. Typical settings:

- `OPTIMIZATION.type_: Adam`
- `OPTIMIZATION.beta1: 0`
- `OPTIMIZATION.beta2: 0.99`
- `OPTIMIZATION.d_first: False`
- `OPTIMIZATION.g_updates_per_step: 1`
- `OPTIMIZATION.d_updates_per_step: 1`
- `STYLEGAN.g_reg_interval`: `4` for StyleGAN2, `1` for StyleGAN3.
- `STYLEGAN.d_reg_interval`: `16`.

`LOSS.apply_r1_reg: True` is expected for StyleGAN2/3. `LOSS.r1_place` must be `inside_loop` or `outside_loop`; `outside_loop` is the paper-style setting.

## StyleGAN2 starting settings

Use these as sanity anchors, then adjust by dataset and memory:

| Regime | `total_steps` | Batch | `d_epilogue_mbstd_group_size` | G/D LR | `r1_lambda` | `g_ema_kimg` | `g_ema_rampup` | `mapping_network` |
| --- | ---: | ---: | ---: | --- | ---: | ---: | --- | ---: |
| 256px paper | 390625 | 64 | 8 | 0.0025 / 0.0025 | 1 | 20 | `N/A` | 8 |
| 512px paper | 390625 | 64 | 8 | 0.0025 / 0.0025 | 0.5 | 20 | `N/A` | 8 |
| 1024px paper | 781250 | 32 | 4 | 0.002 / 0.002 | 2 | 10 | `N/A` | 8 |
| CIFAR | 1562500 | 64 | 32 | 0.0025 / 0.0025 | 0.01 | 500 | 0.05 | 2 |

Additional StyleGAN2 conventions:

- `STYLEGAN.style_mixing_p: 0.9` except CIFAR10/100 where `0` is common.
- `STYLEGAN.apply_pl_reg: True` with `STYLEGAN.pl_weight: 2` except CIFAR10/100 where path length regularization is commonly disabled.
- `STYLEGAN.d_architecture: orig` for CIFAR10/100 and `resnet` for larger images.

## StyleGAN3 starting settings

StyleGAN3 settings generally apply to both `stylegan3-t` and `stylegan3-r`; use dataset-tuned configs when available.

| Resolution | `total_steps` | Batch | `d_epilogue_mbstd_group_size` | G/D LR | `r1_lambda` | `g_ema_kimg` | `g_ema_rampup` | `mapping_network` |
| --- | ---: | ---: | ---: | --- | ---: | ---: | --- | ---: |
| 128px | 781250 | 32 | 4 | 0.0025 / 0.002 | 0.5 | 10 | `N/A` | 2 |
| 256px | 781250 | 32 | 4 | 0.0025 / 0.002 | 2 | 10 | `N/A` | 2 |
| 512px | 781250 | 32 | 4 | 0.0025 / 0.002 | 8 | 10 | `N/A` | 2 |
| 1024px | 781250 | 32 | 4 | 0.0025 / 0.002 | 32 | 10 | `N/A` | 2 |

Additional StyleGAN3 conventions:

- `STYLEGAN.style_mixing_p: 0`.
- `STYLEGAN.apply_pl_reg: False` and `STYLEGAN.pl_weight: 0`.
- `STYLEGAN.d_architecture: resnet`.
- `STYLEGAN.g_reg_interval: 1`.
- For `stylegan3-r`, set `STYLEGAN.blur_init_sigma: 10`.

## ADA, APA, and DiffAug choices

StudioGAN exposes three related limited-data augmentation paths:

| YAML fields | Meaning | Typical choices |
| --- | --- | --- |
| `AUG.apply_ada`, `AUG.ada_aug_type` | Adaptive discriminator augmentation | `ada_aug_type: bgc` is a broad default. |
| `AUG.apply_apa`, `AUG.apa_*` | Adaptive pseudo augmentation | Keep numeric schedule fields aligned with ADA if both are enabled. |
| `AUG.apply_diffaug`, `AUG.diffaug_type` | Differentiable augmentation | Use a supported type such as `diffaug`, `simclr_basic`, or an ADA-pipe token. |

Common ADA schedule:

```yaml
AUG:
  apply_ada: True
  ada_aug_type: "bgc"
  ada_initial_augment_p: 0
  ada_target: 0.6
  ada_kimg: 500
  ada_interval: 4
```

If ADA and APA are both enabled, their initial probability, target, kimg, and interval fields must match exactly.

Supported ADA-pipe tokens include:

- `blit`
- `geom`
- `color`
- `filter`
- `noise`
- `cutout`
- `bg`
- `bgc`
- `bgcf`
- `bgcfn`
- `bgcfnc`

## Mixed precision and custom CUDA ops

StyleGAN2/3 training enables StyleGAN-specific optimized operations when CUDA tensors are used. Practical consequences:

- A CUDA-capable PyTorch build is required for real training.
- Custom op failures usually point to compiler/toolkit compatibility or cache/build permissions, not to an ordinary YAML syntax problem.
- `-mpc` changes StyleGAN internal FP16 resolution settings and disables TF32 matmul/convolution behavior in the StyleGAN path.
- Start with `-metrics none` for infrastructure smoke runs if metric backbone downloads or W&B credentials are not ready.

## StyleGAN-incompatible flags

Compatibility rejects or discourages these with StyleGAN2/3:

- Spectral normalization (`MODEL.apply_g_sn`, `MODEL.apply_d_sn`).
- Non-`Auto` activations.
- `MODEL.g_ema_decay` and `MODEL.g_ema_start` when `MODEL.apply_g_ema` is true; use `STYLEGAN.g_ema_kimg` and `STYLEGAN.g_ema_rampup` instead.
- Attention layers.
- Feature matching, gradient penalty variants, deep regret analysis, ZCR, latent optimization, synchronized BN, batch/standing statistics, FreezeD, Langevin/DDLS, interpolation, and SeFa in the combined compatibility assertion for StyleGAN2/3.

If a task needs post-training visualization or SeFa-like analysis, route to [sampling and analysis](../../sampling-and-analysis/SKILL.md) and re-check the exact backbone support before promising a command.

## Validation checklist

Before launching StyleGAN training:

1. Confirm `DATA.img_size`, `DATA.num_classes`, and conditional settings match the dataset.
2. Confirm `STYLEGAN.d_epilogue_mbstd_group_size <= OPTIMIZATION.batch_size / world_size`.
3. Confirm no spectral normalization and activations are `Auto`.
4. For StyleGAN3, choose `stylegan3-t` or `stylegan3-r`; for `stylegan3-r`, set `blur_init_sigma`.
5. Use StyleGAN EMA fields, not non-StyleGAN EMA fields.
6. If ADA/APA are enabled together, align their schedule fields exactly.
7. Run `validate_studiogan_config.py` with the planned `--gpus`, `--metrics`, `--mixed-precision`, and DDP flags.
