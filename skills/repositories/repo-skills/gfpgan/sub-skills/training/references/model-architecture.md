# GFPGAN Model and Architecture Reference

## Purpose

Read this when explaining GFPGAN model components, verifying constructor signatures, or mapping training config sections to source objects.

## Verified Constructors

```python
GFPGANModel(opt)
FFHQDegradationDataset(opt)
GFPGANv1(out_size, num_style_feat=512, channel_multiplier=1, resample_kernel=(1, 3, 3, 1), decoder_load_path=None, fix_decoder=True, num_mlp=8, lr_mlp=0.01, input_is_latent=False, different_w=False, narrow=1, sft_half=False)
GFPGANv1Clean(out_size, num_style_feat=512, channel_multiplier=1, decoder_load_path=None, fix_decoder=True, num_mlp=8, input_is_latent=False, different_w=False, narrow=1, sft_half=False)
GFPGANBilinear(out_size, num_style_feat=512, channel_multiplier=1, decoder_load_path=None, fix_decoder=True, num_mlp=8, lr_mlp=0.01, input_is_latent=False, different_w=False, narrow=1, sft_half=False)
StyleGAN2GeneratorClean(out_size, num_style_feat=512, num_mlp=8, channel_multiplier=2, narrow=1)
StyleGAN2GeneratorBilinear(out_size, num_style_feat=512, num_mlp=8, channel_multiplier=2, lr_mlp=0.01, narrow=1, interpolation_mode='bilinear')
ResNetArcFace(block, layers, use_se=True)
FacialComponentDiscriminator()
```

## Generator Families

### `GFPGANv1`

The original architecture combines a U-Net encoder path with a StyleGAN2 decoder modulated by SFT (spatial feature transform). It can use BasicSR/StyleGAN2 components that may require extension/JIT support depending on the environment.

### `GFPGANv1Clean`

The clean architecture keeps the GFPGAN U-Net plus StyleGAN prior idea but uses clean PyTorch implementations instead of custom StyleGAN2 CUDA extension paths. It is used by clean inference versions such as `1.2`, `1.3`, and `1.4`.

### `GFPGANBilinear`

The bilinear architecture is important for the fine-tuning/conversion story. The FAQ notes that the clean v1.2 model is converted from a bilinear model; to fine-tune that clean checkpoint, fine-tune the bilinear source and then convert.

### `RestoreFormer`

RestoreFormer is a separate architecture exposed by the inference script. It is relevant to inference/model selection but is not the default GFPGAN training path.

## `GFPGANModel` Training Behavior

`GFPGANModel` is registered in BasicSR's model registry and builds networks/losses from the YAML config.

Important behavior:

- Builds `net_g` from `network_g` and optionally loads `path.pretrain_network_g`.
- In training mode, builds `net_d`, EMA generator, optional component discriminators, and optional identity network.
- Uses pixel, perceptual/style, GAN, component, component-style, identity, image-pyramid, and R1 regularization terms depending on config.
- `feed_data` expects `lq` and usually `gt`; component crops add `loc_left_eye`, `loc_right_eye`, and `loc_mouth`.
- `optimize_parameters(current_iter)` alternates generator/discriminator updates and records losses in `log_dict`.
- `test()` uses `net_g_ema` when available; otherwise it temporarily runs `net_g` in eval mode and returns to training mode.
- `nondist_validation` writes restored validation images and metric summaries when configured.

## Component Discriminators and Identity Network

The full config can include:

- `network_d_left_eye`
- `network_d_right_eye`
- `network_d_mouth`
- `network_identity`

When all component discriminators are present, `GFPGANModel` crops eye/mouth regions with ROI align and applies component adversarial/style losses. When `network_identity` is present, it computes identity loss from grayscale resized outputs with `ResNetArcFace`.

## Architecture Smoke Expectations

Tiny GPU architecture tests in the source evidence instantiate 32x32 networks and verify output shapes such as `(1, 3, 32, 32)`. These are smoke checks for wiring and dependencies, not proof of full-quality restoration or training convergence.
