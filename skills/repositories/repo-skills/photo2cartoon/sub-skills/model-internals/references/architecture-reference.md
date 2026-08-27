# Architecture Reference

Evidence used: `models/networks.py`, `models/UGATIT_sadalin_hourglass.py`, `models/face_features.py`, `models/mobilefacenet.py`, and the CPU synthetic smoke outputs recorded in the environment report.

## Verified source smoke shapes

The source smoke and bundled smoke script exercised the architecture on CPU with synthetic tensors. These are the verified tuple shapes:

| Module | Synthetic input | Returned tuple | Verified note |
| --- | --- | --- | --- |
| `ResnetGenerator(..., light=True)` | `(1, 3, 32, 32)` | `out (1, 3, 32, 32)`, `cam_logit (1, 2)`, `heatmap (1, 1, 8, 8)` | Passed on CPU |
| global `Discriminator(input_nc=3, n_layers=7)` | `(1, 3, 256, 256)` | `out (1, 1, 6, 6)`, `cam_logit (1, 2)`, `heatmap (1, 1, 7, 7)` | Passed on CPU |
| local `Discriminator(input_nc=3, n_layers=5)` | `(1, 3, 256, 256)` | `out (1, 1, 30, 30)`, `cam_logit (1, 2)`, `heatmap (1, 1, 31, 31)` | Passed on CPU |

Discriminator patch-map shapes are input-size dependent; do not hard-code the spatial sizes beyond the tuple order and CAM-channel contract.

## Generator contract

`ResnetGenerator.forward(x)` accepts an RGB tensor shaped `(N, 3, H, W)` and returns a tuple:

1. `out`: cartoon-style RGB tensor with the same spatial size as the input.
2. `cam_logit`: two CAM logits, one from GAP and one from GMP, shaped `(N, 2)`.
3. `heatmap`: single-channel CAM heatmap shaped `(N, 1, h, w)`.

Important implementation facts:

- `ConvBlock1` uses reflection padding, a 7×7 convolution, instance norm, and ReLU.
- `HourGlass1` and `HourGlass2` run before downsampling.
- `DownBlock1` and `DownBlock2` reduce spatial size by 2× each.
- `EncodeBlock1` through `EncodeBlock4` are residual blocks.
- The CAM path computes both adaptive average pooling and adaptive max pooling, then reuses the learned linear weights to reweight feature maps.
- `ConvBlock2` ends with `Tanh`, so the generator output is bounded to approximately `[-1, 1]` before denormalization.
- `HourGlass3` runs with residual fusion and `HourGlass4` is created with `use_res=False`.

## Discriminator contract

`Discriminator.forward(x)` returns the same tuple structure:

1. `out`: patch score map shaped `(N, 1, h', w')`.
2. `cam_logit`: `(N, 2)`.
3. `heatmap`: `(N, 1, h'', w'')`.

Implementation notes:

- The global discriminator in the trainer uses `n_layers=7`.
- The local discriminator in the trainer uses `n_layers=5`.
- Both discriminators use spectral normalization on the conv and linear layers that feed the CAM path.
- The final `out` tensor is a patch map, not a scalar.

## HourGlass modules

The hourglass stack is a recursive down/up block built from `HourGlassBlock` and `ConvBlock`.

- Each `HourGlassBlock` applies four `avg_pool2d(..., 2)` reductions.
- The upward path uses `F.upsample(..., scale_factor=2)` in the source file.
- Skip connections join matching resolution levels: `skip1` through `skip4`.
- `HourGlass(dim_in, dim_out, use_res=True)` returns a residual sum of the input, the transformed branch, and the CAM branch projection.
- `HourGlass(dim_in, dim_out, use_res=False)` returns only the CAM branch output.

For ports or refactors, keep the input size divisible by 16 so the four hourglass pool steps stay aligned.

## Soft-AdaLIN, AdaLIN, and LIN

`ResnetSoftAdaLINBlock` combines convolution, Soft-AdaLIN, ReLU, and a second convolution with another Soft-AdaLIN.

`SoftAdaLIN` behaves as follows:

1. Compute content gamma/beta from the encoder features with small MLPs.
2. Compute style gamma/beta from the decoder features with linear layers.
3. Blend them with learnable mixing weights `w_gamma` and `w_beta`.
4. Feed the blended affine parameters into `adaLIN`.

The exact mixing is:

- `soft_gamma = (1 - w_gamma) * style_gamma + w_gamma * content_gamma`
- `soft_beta = (1 - w_beta) * style_beta + w_beta * content_beta`

`adaLIN` blends instance and layer normalization with `rho`:

- `rho` is initialized to `0.9`.
- `out = rho * IN(x) + (1 - rho) * LN(x)`.
- The normalized tensor is then affine-transformed by `gamma` and `beta`.

`LIN` uses the same blended normalization path, but its affine parameters are learned `gamma` and `beta` tensors with initial values `1.0` and `0.0`.

## Synthetic verification target

A safe smoke check should confirm:

- the generator returns `(out, cam_logit, heatmap)`;
- the output image tensor keeps the same spatial size as the input;
- the output range stays within the `Tanh` bound;
- the CAM logit has width 2;
- the heatmap is single-channel;
- both global and local discriminator classes can be instantiated on CPU.

