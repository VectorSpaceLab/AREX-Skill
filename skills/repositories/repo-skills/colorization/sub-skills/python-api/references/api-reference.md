# Python API reference

This repository exposes the runtime API through the `colorizers` Python package. The package-level `colorizers/__init__.py` re-exports public names from `base_color`, `eccv16`, `siggraph17`, and `util`, so the common entry point is:

```python
import colorizers
```

## Public constructors and wrappers

Verified signatures:

```python
colorizers.BaseColor()
colorizers.ECCVGenerator(norm_layer=BatchNorm2d)
colorizers.SIGGRAPHGenerator(norm_layer=BatchNorm2d, classes=529)
colorizers.eccv16(pretrained=True)
colorizers.siggraph17(pretrained=True)
```

Recommended no-network construction for tests and API inspection:

```python
import colorizers

model_eccv = colorizers.eccv16(pretrained=False).eval()
model_siggraph = colorizers.siggraph17(pretrained=False).eval()
```

The wrapper functions default `pretrained=True`. With that default they call `torch.utils.model_zoo.load_url(..., map_location='cpu', check_hash=True)` and download weights from public `colorizers.s3.us-east-2.amazonaws.com` URLs:

- ECCV 2016 wrapper: `colorization_release_v2-9b330a0b.pth`
- SIGGRAPH 2017 wrapper: `siggraph17-df00044c.pth`

Use `pretrained=False` whenever a smoke test, offline run, or CI check must not make a network call. Instantiating `ECCVGenerator()` or `SIGGRAPHGenerator()` directly also constructs untrained models and does not download weights.

## BaseColor normalization constants

Both model classes inherit from `BaseColor`, which defines these constants:

```python
l_cent = 50.0
l_norm = 100.0
ab_norm = 110.0
```

Methods:

```python
normalize_l(in_l)      # (in_l - 50) / 100
unnormalize_l(in_l)    # in_l * 100 + 50
normalize_ab(in_ab)    # in_ab / 110
unnormalize_ab(in_ab)  # in_ab * 110
```

Callers normally pass raw Lab L/ab tensors. The model `forward` methods perform the needed internal normalization and return unnormalized Lab `ab` outputs.

## Model forward signatures and tensor shapes

Verified signatures:

```python
ECCVGenerator.forward(self, input_l)
SIGGRAPHGenerator.forward(self, input_A, input_B=None, mask_B=None)
```

### ECCVGenerator

Expected input:

- `input_l`: torch tensor shaped `[N, 1, H, W]`.
- Values are raw Lab L-channel values, usually in the Lab L range `0..100`.
- The standard preprocessing helper returns `[1, 1, 256, 256]` for the resized L input when called with its default `HW=(256, 256)`.

Output:

- Lab `ab` tensor shaped `[N, 2, H, W]` for the standard `256 x 256` path; a verified CPU no-download smoke run produced `1 x 2 x 256 x 256`.
- Values are unnormalized Lab `a,b` channels, suitable for `postprocess_tens`.

Minimal forward snippet without downloading weights:

```python
import torch
import colorizers

model = colorizers.eccv16(pretrained=False).eval()
input_l = torch.zeros(1, 1, 256, 256)
with torch.no_grad():
    out_ab = model(input_l)
print(tuple(out_ab.shape))  # (1, 2, 256, 256)
```

### SIGGRAPHGenerator

Expected inputs:

- `input_A`: torch tensor shaped `[N, 1, H, W]`, raw Lab L values.
- `input_B`: optional torch tensor shaped `[N, 2, H, W]`, raw Lab `ab` hint values.
- `mask_B`: optional torch tensor shaped `[N, 1, H, W]`, usually a 0/1 hint mask.

If `input_B` is `None`, the implementation creates a zero `ab` hint tensor from `input_A`. If `mask_B` is `None`, it creates a zero mask from `input_A`. These defaults let the SIGGRAPH model run as an automatic colorizer:

```python
import torch
import colorizers

model = colorizers.siggraph17(pretrained=False).eval()
input_l = torch.zeros(1, 1, 256, 256)
with torch.no_grad():
    out_ab = model(input_l)  # no hints
print(tuple(out_ab.shape))  # (1, 2, 256, 256)
```

Explicit zero-hint call:

```python
input_l = torch.zeros(1, 1, 256, 256)
hints_ab = torch.zeros(1, 2, 256, 256)
hint_mask = torch.zeros(1, 1, 256, 256)
with torch.no_grad():
    out_ab = model(input_l, hints_ab, hint_mask)
```

The implementation concatenates normalized `input_A`, normalized `input_B`, and `mask_B` along the channel dimension. Batch size, height, width, dtype, and device must match across all three tensors.

## Image and Lab helper functions

Verified signatures:

```python
colorizers.load_img(img_path)
colorizers.resize_img(img, HW=(256, 256), resample=3)
colorizers.preprocess_img(img_rgb_orig, HW=(256, 256), resample=3)
colorizers.postprocess_tens(tens_orig_l, out_ab, mode='bilinear')
```

Typical helper pipeline:

```python
import colorizers

img_rgb = colorizers.load_img("image.jpg")
tens_orig_l, tens_rs_l = colorizers.preprocess_img(img_rgb, HW=(256, 256))

model = colorizers.eccv16(pretrained=False).eval()
out_ab = model(tens_rs_l)
img_rgb_out = colorizers.postprocess_tens(tens_orig_l, out_ab)
```

Helper behavior:

- `load_img(img_path)` loads an image with Pillow into a NumPy array. If the loaded image is 2-D grayscale, it tiles the channel into 3 RGB-like channels.
- `resize_img(img, HW=(256, 256), resample=3)` returns a resized NumPy array. `HW` is `(height, width)` even though Pillow receives `(width, height)` internally.
- `preprocess_img(img_rgb_orig, HW=(256, 256), resample=3)` converts both original and resized RGB images to Lab and returns `(tens_orig_l, tens_rs_l)`.
- `tens_orig_l` is shaped `[1, 1, H_orig, W_orig]`; `tens_rs_l` is shaped `[1, 1, HW[0], HW[1]]`.
- `postprocess_tens(tens_orig_l, out_ab, mode='bilinear')` resizes `out_ab` back to the original L size when needed, concatenates L and `ab`, converts Lab to RGB, and returns an `H_orig x W_orig x 3` NumPy RGB array.
- The `mode` parameter exists in the signature; the current implementation uses bilinear interpolation when resizing.

## CPU and CUDA placement

CUDA is optional. For CPU use, keep all tensors and models on CPU. For CUDA use, move the model and every forward input to the same CUDA device:

```python
device = torch.device("cuda")
model = colorizers.siggraph17(pretrained=False).eval().to(device)
input_l = input_l.to(device)
hints_ab = hints_ab.to(device)
hint_mask = hint_mask.to(device)
with torch.no_grad():
    out_ab = model(input_l, hints_ab, hint_mask)

# postprocess_tens concatenates tensors, so use matching devices.
rgb = colorizers.postprocess_tens(tens_orig_l.cpu(), out_ab.cpu())
```
