# Model overview

## High-level pipeline
EdgeConnect is a two-stage inpainting system:
1. the edge generator hallucinates missing structure,
2. the inpaint generator fills RGB content using the edge hint,
3. the joint stage updates both submodels,
4. the edge-inpaint stage uses the edge model as a conditioner while only the inpaint branch is stepped.

## Architecture summary

| Component | Input | Output | Notes |
| --- | --- | --- | --- |
| Edge generator | masked grayscale image, masked edge map, mask | 1-channel edge probability map | encoder → 8 residual blocks → decoder, with spectral norm on the edge path |
| Inpaint generator | masked RGB image, edge map | 3-channel RGB image | encoder → 8 residual blocks → decoder, final `tanh` mapped into `[0, 1]` |
| Discriminator | image/edge pair or RGB image | patch logits plus intermediate feature maps | 5 convolutional blocks with spectral norm |

The generators use reflection padding, instance normalization, and residual blocks. The discriminator is a PatchGAN-style classifier that also returns feature maps for feature matching.

## Losses

### Edge model
- Adversarial loss from `GAN_LOSS`.
- Feature-matching loss on discriminator feature maps, scaled by `FM_LOSS_WEIGHT`.
- No perceptual or style loss.

### Inpaint model
- Adversarial loss, scaled by `INPAINT_ADV_LOSS_WEIGHT`.
- Mask-normalized L1 loss, scaled by `L1_LOSS_WEIGHT`.
- VGG19 perceptual loss, scaled by `CONTENT_LOSS_WEIGHT`.
- VGG19 style loss, scaled by `STYLE_LOSS_WEIGHT`.

`GAN_LOSS` can be `nsgan`, `lsgan`, or `hinge`. The discriminator uses a sigmoid head for the non-hinge variants and a linear head for hinge loss.

## Checkpoints and logs

| File family | Contents | Loaded when |
| --- | --- | --- |
| `EdgeModel_gen.pth` | generator state and saved iteration | when the edge model is used |
| `EdgeModel_dis.pth` | discriminator state | only during training |
| `InpaintingModel_gen.pth` | generator state and saved iteration | when the inpaint model is used |
| `InpaintingModel_dis.pth` | discriminator state | only during training |
| `log_edge.dat` / `log_inpaint.dat` / `log_edge_inpaint.dat` / `log_joint.dat` | space-separated scalar logs | when `LOG_INTERVAL` fires |
| `samples/<stage>/<iteration>.png` | stitched validation sample montage | when `SAMPLE_INTERVAL` fires |

Resume behavior:
- loading reads the generator checkpoint first and restores the iteration counter from it,
- the discriminator checkpoint is loaded only if training mode is active,
- optimizer state is not saved, so Adam momentum is reinitialized on resume.

## Internal metrics
- Edge precision and recall come from `EdgeAccuracy` on the masked region and are thresholded by `EDGE_THRESHOLD`.
- PSNR is computed on the merged RGB output.
- MAE is a relative sum-absolute-error ratio computed on the raw image tensors.

These are internal diagnostics for the training and validation loops. They are not the same as the external PSNR/SSIM/FID scripts.

## Resource and weight caveats
- `PerceptualLoss` and `StyleLoss` instantiate pretrained VGG19 from `torchvision` and may need the cached weights or a networked first run.
- Multi-GPU runs use `DataParallel` when more than one GPU id is listed in `GPU`.
- The runtime sets `CUDA_VISIBLE_DEVICES` from `GPU`, so an empty GPU list gives a CPU-only configuration.
- CPU mode is useful for inspection or tiny smoke runs, but real training is expected to use CUDA.
- The current `MODEL = 3` path always uses predicted edges from the edge model.
