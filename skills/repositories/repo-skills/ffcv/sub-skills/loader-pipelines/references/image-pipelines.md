# Image decoders and image pipelines

FFCV stores RGB images through `RGBImageField` and exposes a decoder operation
for the loader. The decoder emits a batch in HWC layout (`B, H, W, 3`) as
`uint8` NumPy data. Keep raw-array augmentations before tensor conversion;
convert layout and device only when the downstream torch model needs it.

## Decoder catalog

| Decoder | Constructor | Input-resolution contract | Output |
|---|---|---|---|
| `SimpleRGBImageDecoder` | `SimpleRGBImageDecoder()` | Every stored image must have identical height and width. It raises `TypeError` while the graph inspects metadata if either dimension varies. | Original resolution, HWC `uint8`; reads raw or JPEG records. |
| `RandomResizedCropRGBImageDecoder` | `(output_size, scale=(0.08, 1.0), ratio=(0.75, 4/3))` | Variable or constant source resolution is supported. Samples area and aspect ratio, with a center/fallback crop after failed random trials. | Fixed `(output_size[0], output_size[1], 3)` HWC `uint8`. |
| `CenterCropRGBImageDecoder` | `(output_size, ratio)` | Variable or constant source resolution is supported. Crops a centered square whose side is `ratio * min(H, W)`. | Fixed `(output_size[0], output_size[1], 3)` HWC `uint8`. |

`RGBImageField.get_decoder_class()` returns `SimpleRGBImageDecoder`, so an
omitted image pipeline selects the strict decoder. A variable-resolution
fixture therefore must explicitly select a crop decoder even if a later
transform would resize it. Do not try to repair this by adding `ToTensor`:
the decoder's allocation/state check occurs first.

The decoders handle both raw and JPEG records according to image metadata. JPEG
is lossy; exact pixel equality is only an appropriate assertion for raw test
fixtures. The writer's `max_resolution` can normalize source sizes before
loading, but it is a storage choice, not a substitute for understanding the
loader decoder contract.

## Recommended layouts

### CPU-native augmentation then GPU model

```python
import torch
from ffcv.fields.decoders import RandomResizedCropRGBImageDecoder
from ffcv.transforms import (
    RandomHorizontalFlip, RandomTranslate, Cutout,
    ToTensor, ToDevice, ToTorchImage, Convert,
)

image_pipeline = [
    RandomResizedCropRGBImageDecoder((224, 224)),
    RandomHorizontalFlip(0.5),
    RandomTranslate(padding=2),
    Cutout(8, fill=(mean_r, mean_g, mean_b)),
    ToTensor(),
    ToDevice(torch.device('cuda:0'), non_blocking=True),
    ToTorchImage(channels_last=True),
    Convert(torch.float16),
]
```

Before `ToTensor`, the stages see NumPy HWC images and can be Numba compiled.
`ToTensor` changes the state to a CPU torch tensor but preserves HWC shape.
`ToDevice` allocates a device buffer and copies the active batch. `ToTorchImage`
changes the declared state to `(C, H, W)` and returns a BCHW view; with
`channels_last=True` it normally avoids a contiguous copy, while
`channels_last=False` asks for an allocated contiguous BCHW result. A model
converted to channels-last memory format is a natural match for the default.

`non_blocking=True` expresses an asynchronous-capable host-to-device copy; its
benefit depends on available pinned host storage and stream overlap. It does
not make a CPU operation a GPU operation.

### GPU normalization

For uint8 images, use the fast `NormalizeImage` operation rather than a generic
CPU transform when its input contract fits:

```python
[
    SimpleRGBImageDecoder(),
    ToTensor(),
    ToDevice(torch.device('cuda:0')),
    ToTorchImage(),
    NormalizeImage(np.asarray(mean), np.asarray(std), np.float16),
    View(torch.float16),
]
```

The operation chooses CPU or GPU code from the preceding `State.device` during
graph collection. Its GPU path expects BCHW data marked channels-last, uses
CuPy and `pytorch_pfn_extras`, and emits the requested equivalent torch dtype.
Its CPU path is an index-aware NumPy operation and allocates a transformed HWC
buffer; verify the dtype and layout explicitly. `View` is a torch view and must
not be used to pretend an arbitrary dtype conversion is numerically safe.

## Native transform catalog

These operations are designed for raw HWC NumPy images unless stated otherwise:

| Operation | State/memory behavior | Placement and caution |
|---|---|---|
| `RandomHorizontalFlip(p)` | Same shape/dtype; new image allocation. | CPU before `ToTensor`; `p=1.0` is useful for a deterministic fixture. |
| `RandomTranslate(padding, fill)` | Same final image shape/dtype; allocates padded temporary storage. | CPU before tensor conversion. Its implementation fills a padded buffer then selects a random crop. |
| `Cutout(crop_size, fill)` | In-place same shape/dtype. | CPU before tensor conversion; crop must fit H and W. |
| `RandomResizedCrop(scale, ratio, size)` | Fixed square HWC output and an allocation. | CPU post-decode alternative to decoder RRC; prefer decoder RRC when possible so variable source images are resized during decode. |
| `RandomBrightness/Contrast/Saturation(magnitude, p)` | Same shape/dtype and allocated output. | Raw uint8 CPU stages; values clip to `[0,255]`. |
| `NormalizeImage(mean, std, type)` | Changes dtype and allocates; CPU and GPU paths differ. | Put after the layout/device stage required by the selected path. |
| `ImageMixup(alpha, same_lambda)` | Same shape/dtype and allocation; index-aware. | Raw images; pair with a matching label pipeline. Its random seed uses the last batch index, so exact behavior is batch-order dependent. |
| `Poison(mask, alpha, indices, clamp)` | Returns images, using a float32 temporary allocation for selected samples. | Raw images; uses absolute dataset indices, not batch positions. |
| `ModuleWrapper(torch.nn.Module)` | Declares no shape/dtype/device change. | Torch-only. Place after `ToTensor`; use `ToDevice` first for GPU modules. |

`RandomBrightness`, `RandomContrast`, and `RandomSaturation` are not generic
floating-point color transforms: their documented implementations operate on
raw image arrays and blend/clip in the uint8 range. Apply normalization after
them. `ToTorchImage` is a layout operation, not a scaling operation; uint8
values remain in their original range until `Convert`, normalization, or a
module changes them.

## Decoder/pipeline examples

### CIFAR-style training and evaluation

```python
import torch
import torchvision.transforms as transforms
from ffcv.fields.decoders import IntDecoder, SimpleRGBImageDecoder
from ffcv.transforms import (
    Convert, Cutout, RandomHorizontalFlip, RandomTranslate,
    Squeeze, ToDevice, ToTensor, ToTorchImage,
)

label = [IntDecoder(), ToTensor(), ToDevice('cuda:0'), Squeeze()]
image = [SimpleRGBImageDecoder()]
if training:
    image += [RandomHorizontalFlip(), RandomTranslate(2), Cutout(8, tuple(mean))]
image += [ToTensor(), ToDevice('cuda:0'), ToTorchImage(), Convert(torch.float16),
          transforms.Normalize(mean, std)]
```

CIFAR's fixed resolution makes `SimpleRGBImageDecoder` valid. The same code
pattern on an ImageNet-like variable-resolution fixture must replace it with
`RandomResizedCropRGBImageDecoder((224,224))` or `CenterCropRGBImageDecoder`.

### Avoiding mixed-mode mistakes

Bad ordering:

```python
[SimpleRGBImageDecoder(), ToTensor(), RandomHorizontalFlip()]
```

The flip returns/allocates NumPy-style data and is not a torch transform. Good
ordering is the flip before `ToTensor`, or a real torch module after
`ToTorchImage`. Likewise, `torchvision.transforms` modules that expect BCHW
must follow both `ToTensor` and `ToTorchImage`; modules that accept HWC tensors
are an unusual explicit exception and should be tested.

## Image verification

For a raw constant-color synthetic dataset, assert exact values and fixed
shapes after `SimpleRGBImageDecoder`; for JPEG, use a bounded error rather than
equality. For variable sizes, assert that Simple raises and crop decoders emit
the requested shape for both `raw` and `jpg` fixtures. Exercise compiled and
uncompiled CPU paths when changing native operations. A GPU normalization test
should compare CPU reference values after moving the result back to host and
should be skipped or marked optional when the shared GPU is unavailable.

## Evidence anchors

- `ffcv/fields/rgb_image.py`, `ffcv/fields/decoders.py`: image metadata,
  decoder state/allocation, JPEG/raw read paths, and crop behavior.
- `ffcv/transforms/ops.py`, `normalize.py`, `random_resized_crop.py`,
  `flip.py`, `translate.py`, `cutout.py`, `color_jitter.py`, `mixup.py`,
  `poisoning.py`: exact stage contracts and layouts.
- `docs/working_with_images.rst`, `docs/making_dataloaders.rst`, and
  `docs/ffcv_examples/cifar10.rst`: supported construction patterns.
- `tests/test_image_read.py`, `test_rrc.py`, `test_augmentations.py`, and
  `test_image_normalization.py`: raw/JPEG, variable-resolution, augmentation,
  and CPU/GPU normalization evidence.
