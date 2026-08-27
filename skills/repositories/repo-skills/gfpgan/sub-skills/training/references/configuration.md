# GFPGAN Training Configuration Reference

## Purpose

Read this when editing GFPGAN BasicSR-style YAML configs or debugging why `GFPGANModel` and `FFHQDegradationDataset` do not build.

## Config Families

- `train_gfpgan_v1_simple`: training without face-component landmark crops. Use it when the user has FFHQ-style images but not `FFHQ_eye_mouth_landmarks_512.pth`.
- `train_gfpgan_v1`: full training with component crops, facial component discriminators, and identity loss. Use it when the user has the required landmark and pretrained identity/checkpoint files.

## Top-Level Sections

| Section | Purpose | Important fields |
| --- | --- | --- |
| `name` | experiment identifier | Choose a unique run name. |
| `model_type` | BasicSR model registry key | `GFPGANModel`. |
| `num_gpu` | GPU count | `auto` in repo configs; real training expects GPU. |
| `manual_seed` | reproducibility seed | Default `0`. |
| `datasets.train` | training data and degradation | `type: FFHQDegradationDataset`, `dataroot_gt`, `io_backend`, degradation ranges. |
| `datasets.val` | validation pair dataset | `dataroot_lq`, `dataroot_gt`, `scale`, normalization. |
| `network_g` | generator | Usually `GFPGANv1` with `out_size: 512`, `decoder_load_path`, `different_w: true`, `sft_half: true`. |
| `network_d` | StyleGAN2 discriminator | `StyleGAN2Discriminator`. |
| `network_d_left_eye`, `network_d_right_eye`, `network_d_mouth` | component discriminators | Present in full config. |
| `network_identity` | identity model | Present in full config, usually `ResNetArcFace`. |
| `path` | pretrained/resume paths | StyleGAN2 decoder, ArcFace identity, resume state, strict-load options. |
| `train` | optimizers, losses, scheduler | Adam optimizers, pixel/perceptual/GAN/component/identity losses. |
| `val` | validation frequency and metrics | PSNR metric in repo fixture configs. |
| `logger` | logging/checkpoint intervals | TensorBoard/W&B flags and checkpoint frequency. |
| `dist_params` | distributed backend | `nccl` and port in repo configs. |

## Dataset Fields

`datasets.train` for `FFHQDegradationDataset` must include:

- `dataroot_gt`: disk folder or `.lmdb` path.
- `io_backend.type`: `disk` or `lmdb`.
- `mean` / `std`: usually `[0.5, 0.5, 0.5]`.
- `out_size`: usually `512`.
- Degradation fields: `blur_kernel_size`, `kernel_list`, `kernel_prob`, `blur_sigma`, `downsample_range`, `noise_range`, `jpeg_range`.
- Optional color fields: `color_jitter_prob`, `color_jitter_shift`, `color_jitter_pt_prob`, `gray_prob`, `gt_gray`.
- Optional component fields: `crop_components`, `component_path`, `eye_enlarge_ratio`.

## Checkpoint Paths

The full training config typically needs:

- `network_g.decoder_load_path`: StyleGAN2 decoder checkpoint.
- `path.pretrain_network_identity`: ArcFace identity checkpoint when identity loss is enabled.
- Optional `path.pretrain_network_g` / discriminator checkpoints for resuming or fine-tuning.
- `datasets.train.component_path`: landmark `.pth` when `crop_components: true`.

Keep checkpoint paths explicit. Do not assume they exist beside the config.

## Loss Settings

`GFPGANModel` reads and builds these loss groups when present:

- `pixel_opt`: L1 pixel loss.
- `perceptual_opt`: VGG perceptual/style loss.
- `L1_opt`: shared L1 loss used for pyramid, component style, and identity terms.
- `gan_opt`: WGAN softplus generator/discriminator loss.
- `gan_component_opt`: component discriminator loss in full config.
- `comp_style_weight` and `identity_weight`: component style and identity loss weights.

## Training Launcher Shape

The source launcher delegates to BasicSR's training pipeline. Command shape:

```bash
python -m torch.distributed.launch --nproc_per_node=4 --master_port=22021 \
  -m gfpgan.train -opt path/to/train_gfpgan_v1.yml --launcher pytorch
```

Modern PyTorch users may replace the deprecated launcher with an equivalent `torchrun` command if their BasicSR version supports it, but validate against the installed stack before changing launchers.

## Minimal Validation Without Full Training

Use the bundled `scripts/check_env.py` to validate imports and optionally parse a config. Use a tiny fixture for dataset smoke tests. Do not run full training as a verification check unless the user explicitly approved the cost.
