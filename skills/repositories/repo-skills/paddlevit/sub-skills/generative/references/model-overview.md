# GAN model overview

## Family comparison

| Family | Generator input | Shipped image sizes | Generator output | Discriminator | Main source files |
|---|---:|---:|---|---|---|
| TransGAN | `z [B,256]`; `Generator(z, epoch)` | CIFAR10 32 | `[B,3,32,32]` | two-scale pure-transformer `Discriminator`, scalar `[B,1]` | `gan/transGAN/models/ViT_custom.py`, `ViT_custom_scale2.py` |
| Styleformer | `z [B,512]`, `c` accepted; shipped `C_DIM=0` | CIFAR10 32, STL10 48, CelebA 64, LSUN 128 | `[B,3,H,W]` | `StyleGANv2Discriminator`, scalar `[B,1]` | `gan/Styleformer/generator.py`, `discriminator.py` |

The table is a source contract summary, not a promise that a checkpoint for
one row can load into the other. Architecture, image size, latent width,
parameter names, and discriminator design must match.

## TransGAN

The shipped `transgan_cifar10.yaml` sets `IMAGE_SIZE=32`, `LATENT_DIM=256`,
`GF_DIM=1024`, `DF_DIM=384`, `BOTTOM_WIDTH=8`, `PATCH_SIZE=2`, generator depth
`5,4,2`, and discriminator depth 3. The generator:

1. projects `z` through `l1` into `8*8*1024` tokens;
2. adds a learned positional embedding and applies a transformer `StageBlock`;
3. applies two `PixelShuffle(2)`-based token/image upsampling stages, reducing
   the channel width to 256 and then 64;
4. applies a 1x1 convolution from 64 to 3 channels.

Thus 8→16→32 spatial resolution and the normal output shape is `[B,3,32,32]`.
`forward(z, epoch)` accepts the epoch argument but the generator body does not
use it in the inspected implementation. The output layer has no explicit
`tanh`; the source generation/eval scripts nevertheless apply the common
`*127.5 + 128` conversion. Capture min/max before relying on that conversion.

The discriminator in `ViT_custom_scale2.py` builds two RGB patch streams at
related scales, processes each with transformer `DisBlock`s, concatenates the
representations, prepends a class token, and returns a single scalar per
image. With default `DIFF_AUG` disabled, `Discriminator(x, aug=False)` is a
shape-only inference call. During training, `aug=True` and a non-disabled
`DATA.DIFF_AUG` can call the source `DiffAugment` policy.

TransGAN's `gan/transGAN/datasets.py` dispatcher directly wires CIFAR10,
CIFAR100, and ImageNet2012. The neighboring `celeba_dataset.py`,
`stl10_dataset.py`, and `lsun_church_dataset.py` are auxiliary loaders but are
not selected by that dispatcher. Do not claim that the stock TransGAN main
scripts support all four GAN README datasets without adapting and testing the
dispatch path.

## Styleformer generator

The Styleformer config defaults are:

```text
Z_DIM=512, C_DIM=0, W_DIM=512, DEPTH=32
```

A mapping network normalizes the latent's second moment, applies two learned
fully connected layers (the source's `num_layers` default is 2), tracks `w_avg`
while training, and broadcasts W vectors to synthesis blocks. `c_dim=0` means
there is no label embedding in the shipped configs. Passing a label tensor from
an eval helper therefore does not make the model class-conditional.

The synthesis network is organized as resolution blocks. Each block performs
style-modulated channel attention, optional noise, a leaky-ReLU, and at the
last block a style-modulated ToRGB projection. LSUN/CelebA configurations set
`LINFORMER=True` for high-resolution efficiency. The config matrix is:

| YAML | `IMAGE_SIZE` | initial resolution | `NUM_LAYERS` | `G_DICT` | special |
|---|---:|---:|---|---|---|
| `styleformer_cifar10.yaml` | 32 | 8 | `[1,3,3]` | `[1024,512,512]` | standard |
| `styleformer_stl10.yaml` | 48 | 12 | `[1,3,3]` | `[1024,256,64]` | unlabeled data uses class 0 |
| `styleformer_celeba.yaml` | 64 | 8 | `[1,2,1,1]` | `[1024,256,64,64]` | Linformer |
| `styleformer_lsun.yaml` | 128 | 8 | `[1,2,1,1,1]` | `[1024,256,64,64,64]` | Linformer |

Styleformer's source generation function calls `Generator(z, c)`. For a
non-conditional model use an empty/ignored conditioning tensor consistent with
the source helper, and validate the current model's `C_DIM` before changing
that call. The output is NCHW and is postprocessed to uint8 HWC RGB by the
source script.

## Styleformer discriminator

`StyleGANv2Discriminator` first maps RGB through a 1x1 equalized convolution,
then walks from the configured resolution down to 4 with `ResBlock`s. The
residual block contains an equalized 3x3 convolution, a filtered/downsampled
convolution, and a filtered/downsampled skip path. A minibatch standard
 deviation channel is appended before the final 3x3 convolution and two
 equalized linear layers produce one scalar.

Supported channel table entries in the source are 4, 8, 16, 32, 48, 64, 128,
256, 512, and 1024. A custom image size absent from this table fails during
construction. The discriminator requires RGB NCHW input with exactly the
configured spatial size; it is not a generic arbitrary-resolution critic.

## Training objectives and source seams

TransGAN uses a hinge-style loss in the main script:

```text
D: mean(ReLU(1-real_score)) + mean(ReLU(1+fake_score))
G: -mean(fake_score)
```

Styleformer uses a WGAN-GP-like objective, `lambda_gp=10`, and five generator
updates per discriminator update in the main scripts. Its gradient-penalty
helper creates an interpolation with `.cuda()`, which makes CPU training an
invalid substitute in the inspected source. Both training loops use random
latents and mutate/checkpoint state; neither is appropriate for a default
smoke.

The source includes PyTorch-to-Paddle conversion scripts under both GAN
folders and Styleformer `port_weights/`. They depend on extra PyTorch/official
repositories and may download or expect source checkpoints. They are excluded
from this operating skill. If porting is explicitly requested, stop at this
route's boundary and ask for a separate authorized workflow.
