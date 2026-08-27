# Troubleshooting the Python API

## Import errors

Symptom:

```text
ModuleNotFoundError: No module named 'colorizers'
```

Fixes:

- Run Python with the repository root on `PYTHONPATH`.
- Or run the bundled diagnostic with `--repo-root` pointing at a clone that contains the `colorizers/` package.
- Import `colorizers` only after the intended repository/package path has been added to `sys.path`.

The diagnostic helper follows this order:

```bash
python scripts/api_smoke.py --repo-root /path/to/your/colorization/clone --help
python scripts/api_smoke.py --repo-root /path/to/your/colorization/clone
```

Use your own clone path in place of the placeholder path above.

## Dependency names in requirements files

The historical requirement names need correction for normal Python packaging:

- Use `torch`.
- Use `numpy`.
- Use `matplotlib` if running plotting or image-display code.
- Use `pillow`, not `PIL`.
- Use `scikit-image`, not `skimage`.
- Use `ipython`; the modules import `IPython.embed` even though normal API calls do not use it.
- Do not install `argparse` for modern Python; it is part of the standard library.

If importing `colorizers` fails on `IPython`, install `ipython` in the same environment used to import the package.

## Avoiding pretrained downloads

Symptom: an API test unexpectedly tries to access the network or pretrained-weight storage.

Cause: both wrapper functions default to `pretrained=True`:

```python
colorizers.eccv16(pretrained=True)
colorizers.siggraph17(pretrained=True)
```

Fix: pass `pretrained=False` for offline or no-download construction:

```python
model_eccv = colorizers.eccv16(pretrained=False).eval()
model_siggraph = colorizers.siggraph17(pretrained=False).eval()
```

Direct class construction is also no-download:

```python
model = colorizers.ECCVGenerator().eval()
```

## Tensor shape and channel mistakes

Expected model input layouts are channel-first PyTorch tensors:

- ECCV L input: `[N, 1, H, W]`.
- SIGGRAPH L input: `[N, 1, H, W]`.
- SIGGRAPH `input_B`: `[N, 2, H, W]`.
- SIGGRAPH `mask_B`: `[N, 1, H, W]`.

Common mistakes:

- Passing an image array shaped `H x W x 3` directly to a model. Use `preprocess_img` first.
- Dropping the batch dimension or channel dimension, producing `[H, W]` or `[1, H, W]` instead of `[1, 1, H, W]`.
- Passing RGB tensors to the model. The models expect Lab L only, not RGB.
- Passing normalized L values when using the model classes. Forward methods call `normalize_l` internally.

## CPU/CUDA device mismatches

CUDA is optional. If you use CUDA, move the model and every forward input to the same CUDA device:

```python
model = colorizers.siggraph17(pretrained=False).eval().to(device)
input_A = input_A.to(device)
input_B = input_B.to(device)
mask_B = mask_B.to(device)
out_ab = model(input_A, input_B, mask_B)
```

For postprocessing, move tensors to the same device before `postprocess_tens`. CPU is simplest:

```python
rgb = colorizers.postprocess_tens(tens_orig_l.cpu(), out_ab.cpu())
```

If `tens_orig_l` is on CPU and `out_ab` is still on CUDA, `torch.cat` inside `postprocess_tens` can fail.

## Dtype and value-range problems

For helper functions:

- Use RGB image arrays, not BGR arrays.
- Use `H x W x 3` arrays, not channel-first arrays.
- `uint8` `0..255` arrays from Pillow are safe.
- Float RGB arrays should use the usual image range `0..1`.

For model tensors:

- L tensors should contain raw Lab L values, usually `0..100`.
- SIGGRAPH `input_B` should contain raw Lab `ab` values; do not divide by `110` yourself.
- The model output is Lab `ab`, not RGB. Use `postprocess_tens` to obtain RGB.

## SIGGRAPH hint/mask mismatches

Symptoms often include tensor concatenation errors or shape mismatch errors.

Check that:

- `input_A`, `input_B`, and `mask_B` have the same batch size, height, and width.
- `input_B` has exactly 2 channels.
- `mask_B` has exactly 1 channel.
- Hints and masks are on the same device as the model.
- Mask values follow the intended convention, usually `0` for no hint and `1` for a provided hint.

If you do not need hints, omit both optional arguments:

```python
out_ab = model(input_A)
```

The implementation will create zero hints and a zero mask.

## Grayscale and alpha-channel edge cases

`load_img` handles 2-D grayscale images by tiling the single channel into three channels. This lets `preprocess_img` convert the result to Lab.

It does not explicitly strip alpha channels. If an image loads as `H x W x 4`, convert it to RGB before preprocessing. Likewise, if you construct image arrays yourself, provide a 3-channel RGB array.

## Unsupported scope

This runtime API skill covers test-time PyTorch usage. It does not cover training workflows or the unsupported Caffe branch.
