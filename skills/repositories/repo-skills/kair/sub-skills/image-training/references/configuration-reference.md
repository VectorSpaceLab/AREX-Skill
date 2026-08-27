# KAIR training configuration reference

KAIR training options are JSON files with `//` line comments. KAIR's parser removes everything after `//` on each line before calling `json.loads`, then expands paths and injects defaults. Keep edited configs valid after comments are stripped.

## Minimal top-level structure

Most image training configs follow this shape:

```json
{
  "task": "experiment_name",
  "model": "plain",
  "gpu_ids": [0],
  "dist": true,
  "scale": 4,
  "n_channels": 3,
  "sigma": 0,
  "sigma_test": 0,
  "path": {
    "root": "superresolution",
    "pretrained_netG": null,
    "pretrained_netE": null
  },
  "datasets": {
    "train": {
      "name": "train_dataset",
      "dataset_type": "sr",
      "dataroot_H": "trainsets/trainH",
      "dataroot_L": null,
      "H_size": 96,
      "dataloader_shuffle": true,
      "dataloader_num_workers": 8,
      "dataloader_batch_size": 32
    },
    "test": {
      "name": "test_dataset",
      "dataset_type": "sr",
      "dataroot_H": "testsets/set5",
      "dataroot_L": null
    }
  },
  "netG": {
    "net_type": "msrresnet0",
    "init_type": "orthogonal"
  },
  "train": {
    "G_lossfn_type": "l1",
    "G_lossfn_weight": 1.0,
    "G_optimizer_lr": 0.0001,
    "G_scheduler_milestones": [200000, 400000],
    "checkpoint_test": 5000,
    "checkpoint_save": 5000,
    "checkpoint_print": 200
  }
}
```

GAN configs additionally include `netD` and discriminator/perceptual loss keys. SwinIR configs use a larger `netG` block with transformer-specific keys.

## Parser behavior that affects edits

- `task` plus `path.root` determines the experiment directory: `<path.root>/<task>`.
- For training, KAIR derives:
  - `path.models`: `<path.root>/<task>/models`
  - `path.images`: `<path.root>/<task>/images`
  - `path.options`: `<path.root>/<task>/options`
  - `path.log`: `<path.root>/<task>`
- For each dataset phase, KAIR injects `phase`, `scale`, and `n_channels` from top-level keys.
- `dataroot_H`, `dataroot_L`, and explicit `path` values pass through user expansion (`~`), so user-relative paths are allowed.
- `gpu_ids` is converted into `CUDA_VISIBLE_DEVICES` by joining the list with commas.
- `num_gpu` is set to `len(gpu_ids)`.
- Missing defaults are injected for `merge_bn`, `scale`, DDP flags, perceptual loss options, optimizer defaults, strict-loading flags, EMA, and discriminator defaults.

## Top-level keys

| Key | Meaning | Common values / notes |
| --- | --- | --- |
| `task` | Experiment name and checkpoint namespace. | Change this to avoid accidental auto-resume. |
| `model` | Training wrapper selected by `define_Model`. | `plain`, `plain2`, `plain4`, `gan`; `vrt` belongs to the video sub-skill. |
| `gpu_ids` | Devices KAIR exposes to PyTorch. | `[0]`, `[0,1,2,3]`; must match DDP process count for distributed runs. |
| `dist` | Intended distributed flag in config. | The script ultimately uses the command-line `--dist` value for scripts that expose it. |
| `scale` | SR scale factor broadcast to datasets and some networks. | Usually `1`, `2`, `3`, `4`, `8`; SwinIR also has `netG.upscale`. |
| `n_channels` | Image channels broadcast to datasets. | `1` grayscale, `3` color. SwinIR JPEG uses `is_color` instead of the usual key. |
| `sigma`, `sigma_test` | Denoising noise levels. | DnCNN often fixed scalar; FDnCNN/FFDNet/DRUNet often range `[0, 50]` or `[0, 75]`. |
| `merge_bn`, `merge_bn_startpoint` | DnCNN-style batch-norm merge behavior. | Set false for networks without BN. |
| `path` | Experiment root and optional preload fields. | Startup checkpoint auto-discovery can overwrite `pretrained_*`; see `training-workflows.md`. |
| `datasets` | Train/test dataset definitions. | Include `train`; include `test` only when checkpoint-time evaluation is desired and data exists. |
| `netG` | Generator network configuration. | `net_type` must be supported by KAIR's network selector. |
| `netD` | Discriminator configuration for GAN. | Required for `model: gan`; omitted for PSNR training. |
| `train` | Loss, optimizer, scheduler, checkpoint cadence. | Required for every training run. |

## `model` selector meanings

| `model` | Wrapper role | Typical configs |
| --- | --- | --- |
| `plain` | One input image tensor `L` and target `H`; used for most PSNR image restoration. | DnCNN, FDnCNN, DRUNet, MSRResNet, RRDB/RRDBNet, IMDN, SRMD, DPSR, BSRGAN PSNR, SwinIR PSNR/denoise/JPEG. |
| `plain2` | Two inputs, typically image plus condition/noise level. | FFDNet. |
| `plain4` | Four inputs `L`, kernel `k`, scale `sf`, and noise `sigma`. | USRNet. |
| `gan` | Generator plus discriminator, perceptual/adversarial losses, optional EMA. | MSRResNet GAN, BSRGAN GAN, SwinIR real-world GAN. |
| `vrt` | Video model wrapper. | Route to `../video-restoration/SKILL.md`. |

## Image `dataset_type` mappings

| `dataset_type` values | Meaning | Required roots / important keys | Typical model families |
| --- | --- | --- | --- |
| `dncnn`, `denoising` | Fixed-noise AWGN denoising. | `dataroot_H`, `H_size`, `sigma`, `sigma_test`; `dataroot_L` is usually `null`. | DnCNN, SwinIR denoising. |
| `dnpatch` | DnCNN patch-refresh dataset. | `dataroot_H`; refreshes data periodically in the DnCNN loop. | DnCNN train400-style workflows. |
| `fdncnn`, `denoising-noiselevelmap` | Variable-noise denoising with noise-level map. | `dataroot_H`, `sigma` range, `sigma_test`. | FDnCNN, DRUNet configs. |
| `ffdnet`, `denoising-noiselevel` | Variable-noise denoising with explicit noise-level input. | `dataroot_H`, `sigma` range, `sigma_test`; use `model: plain2`. | FFDNet. |
| `sr`, `super-resolution` | Paired or on-the-fly bicubic SISR. | `dataroot_H` required; `dataroot_L` optional. If `dataroot_L` is `null`, LR is synthesized. | MSRResNet, RRDB, IMDN, SwinIR classical/lightweight SR. |
| `srmd` | SRMD degradation training. | `dataroot_H`; optional `dataroot_L`; `sigma`, `sigma_test`, `H_size`. | SRMD. |
| `dpsr`, `dnsr` | DPSR degradation training. | `dataroot_H`; optional `dataroot_L`; `sigma`, `sigma_test`, `H_size`. | DPSR. |
| `usrnet`, `usrgan` | USRNet kernel/scale/noise training. | `dataroot_H`, `H_size`, optional `scales`, `sigma_max`; no paired LR root required. | USRNet with `model: plain4`. |
| `bsrnet`, `bsrgan`, `blindsr` | Blind/real-world degradation synthesis. | `dataroot_H`, `degradation_type`, `H_size`, `lq_patchsize`, `shuffle_prob`, `use_sharp`. | BSRGAN, SwinIR real-world SR. |
| `jpeg` | JPEG compression artifact reduction. | `dataroot_H`, `quality_factor`, `quality_factor_test`, `is_color`, `H_size`. | SwinIR CAR/JPEG. |
| `plain`, `plainpatch` | Generic paired image-to-image datasets. | Both `dataroot_H` and `dataroot_L` must exist and have matching counts. | Custom paired restoration. |

Video dataset types are intentionally excluded here; route VRT/RVRT configs to `../video-restoration/SKILL.md`.

## `netG.net_type` mappings for image training

| `net_type` | Generator family | Key configuration points |
| --- | --- | --- |
| `dncnn` | DnCNN denoiser. | `in_nc`, `out_nc`, `nc`, `nb`, `act_mode`; often grayscale. |
| `fdncnn` | Flexible DnCNN with noise map. | Similar to DnCNN; pair with `dataset_type: fdncnn`. |
| `ffdnet` | FFDNet denoiser. | Pair with `model: plain2` and `dataset_type: ffdnet`. |
| `srmd` | SRMD SISR. | Uses `scale`, `upsample_mode`, `nc`, `nb`; pair with `dataset_type: srmd`. |
| `dpsr` | DPSR SISR. | Uses degradation/noise settings; pair with `dataset_type: dpsr`. |
| `msrresnet0`, `msrresnet1` | Modified SRResNet variants. | Pay attention to the exact variant in checkpoint compatibility. |
| `rrdb` | RRDB generator. | Uses `nc`, `nb`, `gc`, `upsample_mode`. |
| `rrdbnet` | RRDBNet/BSRGAN-style generator. | Uses `nf`, `nb`, `gc`, `sf`/scale-related fields depending on config. |
| `imdn` | IMDN lightweight SISR. | Uses `nc`, `nb`, scale, and upsampling mode. |
| `usrnet` | Deep unfolding USRNet. | Uses `n_iter`, `h_nc`, `nc` list, down/up-sampling modes; requires `model: plain4`. |
| `drunet` | Deep residual U-Net denoiser. | Uses `nc` list, `nb`, `bias`, `downsample_mode`, `upsample_mode`; configs often use `in_nc: 4` for image plus noise map. |
| `swinir` | SwinIR transformer. | Uses `upscale`, `in_chans`, `img_size`, `window_size`, `depths`, `embed_dim`, `num_heads`, `upsampler`, `resi_connection`. |
| `vrt`, `rvrt` | Video restoration transformers. | Excluded from this image training sub-skill; route to `../video-restoration/SKILL.md`. |

## `netD.net_type` mappings for GAN configs

| `net_type` | Use case |
| --- | --- |
| `discriminator_vgg_96`, `discriminator_vgg_128`, `discriminator_vgg_192` | VGG-style discriminators sized for the training patch. |
| `discriminator_vgg_128_SN` | Spectral-normalized VGG variant. |
| `discriminator_patchgan` | PatchGAN discriminator; defaults may be injected for `in_nc`, `base_nc`, `n_layers`, and `norm_type`. |
| `discriminator_unet` | U-Net discriminator used by BSRGAN/SwinIR real-world GAN configs. |

## Training keys

Common generator keys:

- `G_lossfn_type`: `l1`, `l2`, `l2sum`, `ssim`; `charbonnier` is supported by `model_plain` and used in SwinIR JPEG.
- `G_lossfn_weight`: scalar generator loss weight.
- `E_decay`: EMA decay for `netE`; set `0` to disable.
- `G_optimizer_type`: usually `adam`.
- `G_optimizer_lr`, `G_optimizer_wd`, `G_optimizer_clipgrad`.
- `G_optimizer_reuse`: if true and an optimizer checkpoint is discovered, resume optimizer state.
- `G_scheduler_type`: commonly `MultiStepLR`; some model wrappers also support cosine restarts.
- `G_scheduler_milestones`, `G_scheduler_gamma`.
- `G_param_strict`, `E_param_strict`: checkpoint strictness.
- `checkpoint_test`, `checkpoint_save`, `checkpoint_print`: evaluation/save/log cadence in iterations.

GAN-specific keys:

- `F_lossfn_type`, `F_lossfn_weight`, `F_feature_layer`, `F_weights`, `F_use_input_norm`, `F_use_range_norm`: perceptual loss.
- `gan_type`: `gan`, `ragan`, `lsgan`, `wgan`, or `softplusgan`.
- `D_lossfn_weight`, `D_init_iters`, `D_update_ratio`.
- `D_optimizer_type`, `D_optimizer_lr`, `D_optimizer_wd`, `D_optimizer_reuse`.
- `D_scheduler_type`, `D_scheduler_milestones`, `D_scheduler_gamma`.
- `D_param_strict`.

## GPU and distributed keys

- `gpu_ids` is the source of KAIR's `CUDA_VISIBLE_DEVICES` assignment. If the shell has already masked devices, the IDs should be local to that visible set.
- For DDP, `len(gpu_ids)` should match `--nproc_per_node`.
- In DDP loaders, KAIR divides `dataloader_batch_size` and `dataloader_num_workers` by `num_gpu`; choose totals divisible by the GPU count.
- Scripts without a `--dist` parser (`main_train_dncnn.py`, `main_train_usrnet.py`) should not be launched with DDP flags.
- Use a unique `--master_port` when running multiple distributed jobs on the same host.

## Safe edit checklist

Before launching training:

1. Copy, do not overwrite, a known-good option template.
2. Change `task` when changing dataset, model scale, or resume policy.
3. Set `path.root` to a public experiment folder name, not a private absolute path.
4. Set `datasets.train.dataroot_H` and any required `dataroot_L` to paths that exist in the user's checkout or storage.
5. Match `dataset_type`, `model`, and `netG.net_type` using the tables above.
6. For GAN, include `netD` and discriminator/perceptual loss keys.
7. Match `scale` and, for SwinIR, `netG.upscale`.
8. Match `n_channels` / `in_nc` / `out_nc` / SwinIR `in_chans` for grayscale versus color.
9. For DDP, match `gpu_ids`, `--nproc_per_node`, total batch size, and total worker count.
10. Run `scripts/validate_training_config.py --config <config>` from this sub-skill before launching training.
