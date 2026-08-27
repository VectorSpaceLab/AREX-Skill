# Data formats and tensor conventions

The API is a small PyTorch + NumPy/Pillow/scikit-image pipeline around Lab color space. Keep these conventions consistent when calling the package directly.

## RGB image arrays

`load_img(img_path)` returns a NumPy array from Pillow.

- Normal color images are expected as `H x W x 3` RGB arrays.
- 2-D grayscale images are converted by `load_img` into three identical channels with shape `H x W x 3`.
- The helpers expect RGB channel order, not BGR.
- If supplying your own array instead of `load_img`, provide a 3-channel RGB array. Convert RGBA or palette images to RGB before `preprocess_img`.

Common safe forms:

- `uint8` RGB array with values `0..255`, such as Pillow image data.
- Floating RGB array in the usual image range `0..1`.

Avoid channel-first NumPy arrays for helper functions; `preprocess_img` expects image arrays in `H x W x C` layout.

## Resize behavior

Verified signature:

```python
resize_img(img, HW=(256, 256), resample=3)
```

`HW` is ordered as `(height, width)`. The implementation passes `(HW[1], HW[0])` to Pillow internally, because Pillow resize dimensions are `(width, height)`.

The standard inference preprocessing path uses `HW=(256, 256)`, yielding a resized L tensor shaped `[1, 1, 256, 256]`.

## Lab preprocessing outputs

Verified signature:

```python
preprocess_img(img_rgb_orig, HW=(256, 256), resample=3)
```

Return value:

```python
tens_orig_l, tens_rs_l = preprocess_img(img_rgb_orig, HW=(256, 256))
```

- `tens_orig_l`: `torch.Tensor` shaped `[1, 1, H_orig, W_orig]`.
- `tens_rs_l`: `torch.Tensor` shaped `[1, 1, HW[0], HW[1]]`.
- Both tensors contain raw Lab L-channel values. The L channel is usually in the `0..100` Lab lightness range.
- Do not pre-normalize these L tensors before calling `ECCVGenerator.forward` or `SIGGRAPHGenerator.forward`; both models call `normalize_l` internally.

## Model outputs and ab scale

Both model forward methods return Lab `ab` tensors, not RGB images.

- ECCV: `ECCVGenerator.forward(input_l)` returns an `ab` tensor shaped `[N, 2, H, W]` on the normal `256 x 256` path.
- SIGGRAPH: `SIGGRAPHGenerator.forward(input_A, input_B=None, mask_B=None)` returns an `ab` tensor shaped `[N, 2, H, W]` on the normal `256 x 256` path.
- The returned `ab` values are unnormalized Lab `a,b` values because the models apply `unnormalize_ab` before returning.
- A verified CPU no-download smoke check constructed both models with `pretrained=False` and produced `1 x 2 x 256 x 256` `ab` tensors for `1 x 1 x 256 x 256` L inputs.

## Postprocessing to RGB

Verified signature:

```python
postprocess_tens(tens_orig_l, out_ab, mode='bilinear')
```

Expected inputs:

- `tens_orig_l`: original-size L tensor shaped `[1, 1, H_orig, W_orig]`.
- `out_ab`: colorizer output shaped `[1, 2, H, W]`.

Behavior:

1. If `out_ab` spatial size differs from `tens_orig_l`, it is resized to `(H_orig, W_orig)`.
2. The original L tensor and resized `ab` tensor are concatenated into Lab.
3. Lab is converted to RGB.
4. The returned value is a NumPy array shaped `H_orig x W_orig x 3`.

The RGB output from `skimage.color.lab2rgb` is floating point and normally in the display range `0..1`. Clip before saving if later operations introduce small numeric excursions.

Device caution: `postprocess_tens` concatenates `tens_orig_l` and `out_ab`. Put them on the same device first; moving both to CPU before postprocessing is the simplest pattern.

## SIGGRAPH hints and masks

SIGGRAPH optional arguments:

```python
SIGGRAPHGenerator.forward(input_A, input_B=None, mask_B=None)
```

Shapes:

- `input_A`: `[N, 1, H, W]` raw Lab L.
- `input_B`: `[N, 2, H, W]` raw Lab `ab` hints.
- `mask_B`: `[N, 1, H, W]` mask channel, conventionally `0` for no hint and `1` for a provided hint.

If `input_B` is omitted, it is replaced with zeros matching `input_A` spatial size and batch size. If `mask_B` is omitted, it is also replaced with zeros. This makes the SIGGRAPH model usable with no hints.

Important consistency rules:

- `input_A`, `input_B`, and `mask_B` must share batch size, height, width, dtype family, and device.
- Do not normalize `input_B` yourself; the model calls `normalize_ab(input_B)` internally.
- A mask without meaningful `input_B` values still becomes an input channel. Keep mask and hints aligned.

Minimal explicit-hint skeleton:

```python
input_A = tens_rs_l                    # [1, 1, H, W]
input_B = torch.zeros(1, 2, H, W)      # raw Lab ab hints
mask_B = torch.zeros(1, 1, H, W)       # no hints active
out_ab = model(input_A, input_B, mask_B)
```
