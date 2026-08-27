# StudioGAN configuration reference

StudioGAN merges a YAML file over built-in defaults, then injects CLI flags into the `RUN` section before calling `check_compatability`. A small YAML can therefore rely on many defaults, but compatibility errors often come from interactions among YAML fields, CLI flags, and GPU world size.

Use the bundled validator before running training:

```bash
python sub-skills/training-and-configuration/scripts/validate_studiogan_config.py \
  --repo-root /path/to/PyTorch-StudioGAN \
  --cfg /path/to/config.yaml \
  --data-dir /path/to/data \
  --save-dir /path/to/save \
  --train --metrics fid --gpus 1
```

## YAML sections

Recognized top-level sections:

| Section | Purpose | Common fields |
| --- | --- | --- |
| `DATA` | Dataset identity and image shape | `name`, `img_size`, `num_classes`, `img_channels` |
| `MODEL` | Generator/discriminator architecture and conditioning | `backbone`, `g_cond_mtd`, `d_cond_mtd`, `aux_cls_type`, `apply_g_sn`, `apply_d_sn`, `apply_attn`, `z_dim`, `w_dim`, `g_shared_dim`, `g_conv_dim`, `d_conv_dim`, `apply_g_ema` |
| `LOSS` | Adversarial loss and regularizers | `adv_loss`, `cond_lambda`, `apply_r1_reg`, `r1_place`, `apply_gp`, `apply_cr`, `apply_bcr`, `apply_topk`, `temperature` |
| `OPTIMIZATION` | Optimizer, batch size, update schedule | `type_`, `batch_size`, `acml_steps`, `g_lr`, `d_lr`, `beta1`, `beta2`, `d_first`, `g_updates_per_step`, `d_updates_per_step`, `total_steps` |
| `PRE` | Dataset preprocessing | `apply_rflip` |
| `AUG` | DiffAug, ADA, APA, CR/BCR augment types | `apply_diffaug`, `diffaug_type`, `apply_ada`, `ada_aug_type`, `ada_target`, `apply_apa`, `apa_target` |
| `RUN` | Usually injected from CLI, not hand-authored | `data_dir`, `save_dir`, `ckpt_dir`, `train`, `load_train_hdf5`, `load_data_in_memory`, `eval_metrics`, DDP/mixed precision flags |
| `STYLEGAN` | StyleGAN2/3-specific settings | `stylegan3_cfg`, `g_reg_interval`, `d_reg_interval`, `mapping_network`, `style_mixing_p`, `g_ema_kimg`, `g_ema_rampup`, `apply_pl_reg`, `d_architecture`, `blur_init_sigma` |

Unknown attributes in a section are rejected with a message like `There does not exist 'SECTION.attr' attribute in the config.py.`

## Defaults that matter

Important defaults when a YAML omits fields:

| Field | Default | Consequence |
| --- | --- | --- |
| `DATA.name` | `CIFAR10` | CIFAR10 auto-download behavior applies unless overridden. |
| `DATA.img_size` | `32` | Required by `deep_conv`; custom data may need update. |
| `DATA.num_classes` | `10` | Must match ImageFolder class count for conditional models. |
| `MODEL.backbone` | `resnet` | YAML examples often override to `big_resnet` or `stylegan2/3`. |
| `MODEL.g_cond_mtd` / `MODEL.d_cond_mtd` | `W/O` / `W/O` | Conditional datasets need consistent conditioning choices. |
| `MODEL.apply_g_sn` / `MODEL.apply_d_sn` | `False` / `False` | Some BigGAN-deep configs require spectral normalization. |
| `MODEL.z_dim` | `128` | StyleGAN2/3 uses `512`. CIFAR BigGAN examples may use smaller values. |
| `LOSS.adv_loss` | `vanilla` | Most BigGAN examples use `hinge`; StyleGAN examples use `logistic`. |
| `OPTIMIZATION.batch_size` | `64` | Must divide GPU world size; effective basket size also multiplies by accumulation and discriminator updates. |
| `OPTIMIZATION.d_updates_per_step` | `5` | Many non-StyleGAN configs rely on this default. StyleGAN configs typically set `1`. |
| `OPTIMIZATION.total_steps` | `100000` | Published configs may use much larger values. |
| `PRE.apply_rflip` | `True` | Random horizontal flip in the train transform. |

## Catalog summary

The generated config catalog contains 196 YAML files across these dataset directories:

| Dataset directory | Count | Notes |
| --- | ---: | --- |
| `CIFAR10` | 72 | Largest catalog; many ResNet/BigGAN/StyleGAN variants. |
| `CIFAR100` | 47 | Includes `CIFAR100` and a few `CIFAR1000` data-name configs. |
| `ImageNet` | 19 | BigGAN, BigGAN-Deep, ContraGAN, ACGAN, MHGAN, StyleGAN variants. |
| `CUB200` | 18 | Conditional ImageFolder-style configs. |
| `AFHQv2` | 15 | BigGAN and StyleGAN2/3 high-resolution configs with ADA/APA/DiffAug options. |
| `Baby_ImageNet` | 7 | ImageNet-family subset configs. |
| `Papa_ImageNet` | 7 | ImageNet-family subset configs. |
| `Grandpa_ImageNet` | 7 | ImageNet-family subset configs. |
| `AFHQ` | 2 | StyleGAN2 ADA configs. |
| `FFHQ` | 2 | StyleGAN2 configs. |

Backbones represented in the catalog include:

- `deep_conv`
- `resnet`
- `big_resnet`
- `big_resnet_deep_legacy`
- `big_resnet_deep_studiogan`
- `stylegan2`
- `stylegan3`

Common conditioning/loss patterns:

| Pattern | Typical use |
| --- | --- |
| `g_cond_mtd: cBN`, `d_cond_mtd: PD`, `adv_loss: hinge` | BigGAN/SNGAN-style conditional training. |
| `d_cond_mtd: 2C` or `D2DCE`, `adv_loss: hinge` | ContraGAN/ReACGAN-style conditional configs. |
| `g_cond_mtd: cAdaIN`, `d_cond_mtd: SPD`, `adv_loss: logistic` | Conditional StyleGAN2/3 configs. |
| `g_cond_mtd: W/O`, `d_cond_mtd: W/O`, `adv_loss: logistic` | Unconditional StyleGAN2/3 paper-style configs. |
| `d_cond_mtd: MH`, `adv_loss: MH` | Multi-Hinge GAN; both fields must be `MH`. |

## Choosing a starting config

1. Match `DATA.name` and `img_size` first.
2. Match `num_classes` to the dataset. For custom ImageFolder data, run the dataset checker and update `DATA.num_classes` if needed.
3. Choose a backbone family:
   - `deep_conv`: only for 32x32 data.
   - `resnet`: standard small/medium image GAN baseline.
   - `big_resnet`: BigGAN-family conditional training.
   - `big_resnet_deep_legacy` or `big_resnet_deep_studiogan`: deeper BigGAN variants; require spectral normalization settings.
   - `stylegan2` or `stylegan3`: high-fidelity StyleGAN workflows; see [StyleGAN ADA guide](stylegan-ada-guide.md).
4. Preserve compatible conditioning and loss settings from the chosen family.
5. Adjust `OPTIMIZATION.batch_size` for GPU count before DDP/DP.
6. Run `validate_studiogan_config.py` with the planned CLI flags.

## CLI-injected RUN fields

`src/main.py` creates parser defaults, then updates `cfgs.RUN`. The validator fills the same kind of defaults. Important `RUN` fields:

| CLI flag | RUN field | Default | Notes |
| --- | --- | --- | --- |
| `-data` | `data_dir` | `None` | Required unless only saving fake images. |
| `-save` | `save_dir` | current directory | Outputs are rooted here. |
| `-ckpt` | `ckpt_dir` | `None` | Required for eval-only and freezeD. |
| `-best` | `load_best` | `False` | Select best checkpoint naming. |
| `-DDP` | `distributed_data_parallel` | `False` | Rejected when world size is one. |
| `--backend` | `backend` | `nccl` | DDP backend. |
| `-tn` / `-cn` | `total_nodes` / `current_node` | `1` / `0` | Multi-node DDP. |
| `-sync_bn` | `synchronized_bn` | `False` | Sync BN conversion for multi-GPU. |
| `-mpc` | `mixed_precision` | `False` | Mixed precision training. |
| `-t` | `train` | `False` in parser | The validator defaults to train unless `--eval-only` is selected. |
| `-hdf5` | `load_train_hdf5` | `False` | Build/use train HDF5. |
| `-l` | `load_data_in_memory` | `False` | Requires `-hdf5`. |
| `-metrics` | `eval_metrics` | `['fid']` | Allowed entries: `is`, `fid`, `prdc`, `none`. |
| `--pre_resizer` | `pre_resizer` | `wo_resize` | Auto-forced to no resize for CIFAR/Tiny ImageNet. |
| `--post_resizer` | `post_resizer` | `legacy` | `legacy`, `clean`, or `friendly`. |
| `--eval_backbone` | `eval_backbone` | `InceptionV3_tf` | Metric backbone. |
| `-ref` | `ref_dataset` | `train` | CIFAR allows `train`/`test`; ImageFolder usually `train`/`valid`. |
| `--freezeD` | `freezeD` | `-1` | Requires `-ckpt` when non-negative. |
| `-std_stat`, `-std_max`, `-std_step` | standing statistics fields | disabled | Evaluation-time batch-norm statistics trick. |
| `--print_freq`, `--save_freq` | logging/save intervals | `100`, `2000` | `save_freq` must divide by `print_freq`. |

## Compatibility rules and messages

Use this table to convert common assertion messages into fixes.

| Message or condition | Meaning | Fix |
| --- | --- | --- |
| `-metrics option can only contain is, fid, prdc or none` | Unsupported metric token. | Use a subset of `is fid prdc` or use `none`. |
| `load_data_in_memory option is appliable with the load_train_hdf5 (-hdf5) option` | `-l` was used without HDF5. | Add `-hdf5` or remove `-l`. |
| `deep_conv ... spatial resolution is not 32` | `deep_conv` only supports 32x32. | Use 32x32 data or choose another backbone. |
| `big_resnet_deep ... without applying spectral normalization` | BigGAN-deep config missing SN compatibility. | Set generator/discriminator SN fields according to a known BigGAN-deep config. |
| `Freezing discriminator needs a pre-trained model` | `--freezeD` missing `-ckpt`. | Add `-ckpt /path/to/source_checkpoint`. |
| `Specify -ckpt CHECKPOINT_FOLDER to evaluate GAN without training` | Eval-only requested with metrics and no checkpoint. | Add `-ckpt`, or pass `-t`, or use `-metrics none` for no eval. |
| `StudioGAN does not support ... with DDP` | DDP combined with analysis/CAS/Langevin flags. | Train with DDP, then run analysis later with single GPU/DP. |
| `StudioGAN does not support calculating iFID using hdf5 data format without load_data_in_memory` | iFID with HDF5 needs memory loading. | Add `-l` with `-hdf5`, or do not use HDF5 for iFID. |
| `batch_size should be divided by 8` | Analysis/CAS path requires batch size multiple of 8. | Edit `OPTIMIZATION.batch_size`. |
| `Cannot perform distributed training with a single gpu` | `-DDP` set but world size is one. | Expose multiple GPUs or remove `-DDP`. |
| `Batch_size should be divided by the number of gpus` | Batch size not divisible by world size. | Choose batch size divisible by visible GPUs times total nodes. |
| `RUN.save_freq should be divided by RUN.print_freq` | Logging interval mismatch. | Adjust `--save_freq` or `--print_freq`. |
| `The interpolation filter ...` | Invalid `--pre_resizer`. | Use `wo_resize`, `nearest`, `bilinear`, `bicubic`, or `lanczos`. |
| `resizing flag should be in [legacy, clean, friendly]` | Invalid `--post_resizer`. | Use `legacy`, `clean`, or `friendly`. |

## Conditioning and loss compatibility

- `MODEL.aux_cls_type` values other than `W/O` require classifier-based discriminator conditioning: `AC`, `2C`, or `D2DCE`.
- Multi-Hinge GAN requires both `MODEL.d_cond_mtd` and `LOSS.adv_loss` to be `MH`; TopK is not supported for MHGAN.
- `MODEL.g_shared_dim` is for `big_resnet` and BigGAN-deep backbones.
- `MODEL.g_conv_dim` and `MODEL.d_conv_dim` control dimensions for `resnet`, `big_resnet`, and BigGAN-deep backbones.
- InfoGAN fields must all be `N/A` when `MODEL.info_type` is `N/A`; otherwise the corresponding counts and loss weights must be positive values.

## Augmentation compatibility

- `AUG.apply_diffaug` requires a non-`W/O` `diffaug_type`.
- Consistency regularization (`LOSS.apply_cr`) requires a non-`W/O` `cr_aug_type`.
- Balanced consistency regularization (`LOSS.apply_bcr`) requires a non-`W/O` `bcr_aug_type`.
- ADA and APA may not disagree on initial probability, target, kimg, or interval when both are enabled.
- Do not turn on CR, BCR, and ZCR combinations that the compatibility check rejects.

## StyleGAN compatibility quick rules

Full guidance is in [StyleGAN ADA guide](stylegan-ada-guide.md). Critical rules:

- `MODEL.backbone` must be `stylegan2` or `stylegan3`.
- `MODEL.g_act_fn` and `MODEL.d_act_fn` must be `Auto`.
- Spectral normalization is not supported for StyleGAN2/3.
- `MODEL.g_cond_mtd` is only `W/O` or `cAdaIN`.
- `MODEL.d_cond_mtd: SPD` and `MODEL.g_cond_mtd: cAdaIN` are StyleGAN2/3-only.
- StyleGAN3 requires `STYLEGAN.stylegan3_cfg` in `stylegan3-t` or `stylegan3-r`.
- StyleGAN3-r requires `STYLEGAN.blur_init_sigma`.
- StyleGAN2/3 use `STYLEGAN.g_ema_kimg` and `STYLEGAN.g_ema_rampup`, not `MODEL.g_ema_decay` and `MODEL.g_ema_start`.
- `STYLEGAN.d_epilogue_mbstd_group_size` must be less than or equal to per-GPU batch size.
