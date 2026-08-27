# SimMIM API Reference

## `MaskGenerator`

```text
MaskGenerator(input_size=192, mask_patch_size=32, model_patch_size=4, mask_ratio=0.6)
```

Constraints:

- `input_size % mask_patch_size == 0`
- `mask_patch_size % model_patch_size == 0`

It creates a 2D binary mask over model patches. The number of masked coarse patches is `ceil(token_count * mask_ratio)`.

## `SimMIMTransform`

Converts PIL images to RGB, applies random resized crop and horizontal flip, normalizes with ImageNet mean/std, and returns `(image, mask)`.

## `SimMIM`

```text
SimMIM(config, encoder, encoder_stride, in_chans, patch_size)
```

The forward path:

1. Encodes an image with masked tokens.
2. Decodes with a `1x1` convolution plus pixel shuffle.
3. Expands the mask back to pixel resolution.
4. Optionally normalizes targets.
5. Computes masked L1 reconstruction loss.

## `build_simmim(config)`

Supports `MODEL.TYPE` values `swin` and `swinv2`. Other model types raise `NotImplementedError` for SimMIM pretraining.
