# Translation API Reference

This reference covers the public TLLib translation components that can be used from an installed `tllib` package without relying on source-tree example scripts.

## Import map

```python
import torch
import torch.nn as nn

import tllib.translation.cyclegan as cyclegan
from tllib.translation.cycada import SemanticConsistency
from tllib.translation.fourier_transform import FourierTransform, low_freq_mutate
from tllib.translation.spgan import SiameseNetwork, ContrastiveLoss
from tllib.translation.cyclegan.util import ImagePool, set_requires_grad
```

## CycleGAN generators

Factories are in `tllib.translation.cyclegan` and return initialized `torch.nn.Module` objects.

| Factory | Signature shape | Use |
| --- | --- | --- |
| `cyclegan.resnet_9(ngf, input_nc=3, output_nc=3, norm='batch', use_dropout=False, init_type='normal', init_gain=0.02)` | Tensor `N x input_nc x H x W` -> `N x output_nc x H x W` | ResNet generator with 9 residual blocks; common for larger image-to-image style translation. |
| `cyclegan.resnet_6(...)` | Same as above | Smaller ResNet generator with 6 residual blocks. |
| `cyclegan.unet_256(ngf, input_nc=3, output_nc=3, norm='batch', use_dropout=False, ...)` | Image size should be compatible with 256-pixel U-Net downsampling. | U-Net generator for 256-style inputs. |
| `cyclegan.unet_128(...)` | Image size should be compatible with 128-pixel U-Net downsampling. | U-Net generator for 128-style inputs. |

Important parameters:

- `ngf`: base generator filter count. Benchmark-scale configs often use `64`; component tests can use a smaller value.
- `norm`: one of `batch`, `instance`, or `none`. Checkpoints are architecture- and norm-specific.
- Outputs pass through `tanh`, so generated tensors are in approximately `[-1, 1]` before denormalization.

Minimal component use:

```python
generator = cyclegan.resnet_6(ngf=8, norm='instance')
generator.eval()
x = torch.randn(2, 3, 64, 64)
with torch.no_grad():
    y = generator(x)
assert y.shape == x.shape
```

## CycleGAN discriminators

| Factory | Signature | Output |
| --- | --- | --- |
| `cyclegan.patch(ndf, input_nc=3, norm='batch', n_layers=3, init_type='normal', init_gain=0.02)` | PatchGAN discriminator. | `N x 1 x h x w` raw prediction map. |
| `cyclegan.pixel(ndf, input_nc=3, norm='batch', init_type='normal', init_gain=0.02)` | 1x1 PixelGAN discriminator. | `N x 1 x H x W` raw prediction map. |

Discriminator outputs are raw scores/logits. Do not add a final sigmoid when using TLLib GAN losses.

## CycleGAN losses and utilities

### GAN losses

All three losses are `torch.nn.Module` objects called as `loss(prediction, real=True_or_false)`.

- `cyclegan.LeastSquaresGenerativeAdversarialLoss(reduction='mean')`: LSGAN/MSE target of ones for real and zeros for fake.
- `cyclegan.VanillaGenerativeAdversarialLoss(reduction='mean')`: binary cross entropy with logits; input must be un-sigmoided.
- `cyclegan.WassersteinGenerativeAdversarialLoss(reduction='mean')`: returns `-prediction.mean()` for real and `prediction.mean()` for fake.

Cycle-consistency and identity losses are not special TLLib classes; use normal PyTorch losses such as `nn.L1Loss()`.

```python
net_d = cyclegan.patch(ndf=8, norm='instance')
pred = net_d(torch.randn(2, 3, 64, 64))
gan_loss = cyclegan.LeastSquaresGenerativeAdversarialLoss()
loss_real = gan_loss(pred, real=True)
loss_fake = gan_loss(pred, real=False)
```

### `ImagePool(pool_size)`

Stores previously generated images and sometimes returns a buffered image instead of the latest one, matching standard CycleGAN discriminator training. Use `pool_size=0` to disable buffering.

```python
pool = ImagePool(pool_size=50)
fake_for_discriminator = pool.query(fake_images.detach())
```

### `set_requires_grad(net, requires_grad=False)`

Toggles every parameter in a module. In adversarial training, freeze discriminators while updating generators, then re-enable them for discriminator updates.

## `Translation` PIL transform

`cyclegan.Translation(generator, device=torch.device('cpu'), mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))` wraps a generator as a PIL-image transform.

Input/output contract:

- Input: `PIL.Image` in `H x W x C`; convert to RGB before use if the source may be grayscale/RGBA.
- Preprocess: `ToTensor()` then normalize by `mean/std`.
- Generator input: `1 x C x H x W` on `device`.
- Output: PIL image after denormalization and `ToPILImage()`.

Safe use pattern:

```python
from PIL import Image

net_g = cyclegan.resnet_6(ngf=8, norm='instance')
net_g.eval()
set_requires_grad(net_g, False)
translate = cyclegan.Translation(net_g, device=torch.device('cpu'))

image = Image.new('RGB', (64, 64), color=(120, 80, 200))
with torch.no_grad():
    translated = translate(image)
assert translated.mode == 'RGB'
```

Checkpoint loading pattern:

```python
net_g = cyclegan.resnet_9(ngf=64, norm='instance')
checkpoint = torch.load(checkpoint_path, map_location='cpu')
state = checkpoint.get('netG_S2T', checkpoint)
# If a DataParallel checkpoint adds a "module." prefix, strip it before loading.
state = {k.replace('module.', '', 1): v for k, v in state.items()}
net_g.load_state_dict(state, strict=True)
net_g.eval()
```

The generator factory (`resnet_9`, `unet_256`, etc.), `ngf`, `norm`, and channel counts must match the checkpoint.

## FDA: `FourierTransform` and `low_freq_mutate`

### `low_freq_mutate(amp_src, amp_trg, beta=1)`

Replaces a centered low-frequency square in the source amplitude with the target amplitude. Inputs are NumPy arrays shaped `C x H x W`. Source and target amplitude arrays must have the same channel count and spatial size.

```python
import numpy as np
amp_src = np.ones((3, 32, 32), dtype=np.float32)
amp_trg = np.ones((3, 32, 32), dtype=np.float32) * 2
mutated = low_freq_mutate(amp_src, amp_trg, beta=1)
assert mutated.shape == amp_src.shape
```

### `FourierTransform(image_list, amplitude_dir, beta=1, rebuild=False)`

Builds or reuses `.npy` amplitude files from target-domain images, then translates each source PIL image by mixing target-domain low-frequency amplitude with source phase.

Input/output contract:

- `image_list`: non-empty sequence of readable target image file paths.
- `amplitude_dir`: writable directory for cached target amplitudes named `0.npy`, `1.npy`, ... .
- Input to `forward`: PIL image or array-convertible RGB image from the source domain.
- Output: RGB PIL image with values clipped to `[0, 255]`.
- Source and target image sizes should match before FDA. For segmentation, apply FDA before random crop/resized crop and after resizing source images to the target size.
- TLLib uses integer `beta`; the documented recommended value is `1`.

```python
from PIL import Image
from tempfile import TemporaryDirectory
from pathlib import Path

with TemporaryDirectory() as tmp:
    root = Path(tmp)
    target = root / 'target.png'
    source = root / 'source.png'
    Image.new('RGB', (32, 32), color=(10, 120, 200)).save(target)
    Image.new('RGB', (32, 32), color=(200, 80, 20)).save(source)

    fda = FourierTransform([str(target)], str(root / 'amplitudes'), beta=1, rebuild=True)
    out = fda(Image.open(source).convert('RGB'))
    assert out.size == (32, 32)
```

## CyCADA semantic consistency

`SemanticConsistency(ignore_index=(), reduction='mean')` wraps cross entropy for semantic consistency between translated-image predictions and source labels. It sets ignored class indices to `-1` before applying `nn.CrossEntropyLoss(ignore_index=-1)`.

Input shapes:

- `input`: logits shaped `N x C` or `N x C x H x W`.
- `target`: labels shaped `N` or `N x H x W`.
- Output: scalar unless `reduction='none'`.

Caution: the implementation edits `target` in place. Clone labels before calling when the original labels are needed later.

```python
criterion = SemanticConsistency(ignore_index=(255,))
logits = torch.randn(2, 4, 8, 8)
labels = torch.randint(0, 4, (2, 8, 8))
labels[0, 0, 0] = 255
loss = criterion(logits, labels.clone())
```

## SPGAN Siamese and contrastive pieces

SPGAN adds identity-similarity constraints to CycleGAN-style re-identification translation.

### `SiameseNetwork(nsf=64)`

Returns normalized feature vectors. The implementation has a fixed first fully connected input size of `2048`, so the default re-id tensor shape `N x 3 x 256 x 128` with `nsf=64` is the safe operating shape. Changing image sizes or `nsf` can cause a matrix-size mismatch unless the network is modified.

```python
siamese = SiameseNetwork(nsf=64)
siamese.eval()
with torch.no_grad():
    features = siamese(torch.randn(2, 3, 256, 128))
assert features.shape == (2, 64)
```

### `ContrastiveLoss(margin=2.0)`

Called as `loss(output1, output2, label)`, where `output1` and `output2` are `N x F` feature tensors and `label` is a tensor shaped `N`. TLLib's convention in the SPGAN workflow is `0` for positive/same-identity pairs and `1` for negative/different-domain or different-identity pairs.

```python
criterion = ContrastiveLoss(margin=2.0)
positive = torch.zeros(2)
negative = torch.ones(2)
loss_pos = criterion(features, features, positive)
loss_neg = criterion(features, torch.flip(features, dims=[0]), negative)
```

## Compatibility notes

- CPU component checks are sufficient for API validation; realistic CycleGAN/SPGAN training is GPU- and data-heavy.
- TLLib 0.4 is from an older PyTorch/TorchVision era. If imports or model factories fail under modern dependencies, use the repository-level troubleshooting guidance before debugging algorithm code.
- Optional object-detection and benchmark stacks are not required for the translation component APIs described here.
