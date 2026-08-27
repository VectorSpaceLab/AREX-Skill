# Image and Tensor Utilities

Evidence used: `utils/utils.py`, `test.py`, `test_onnx.py`, `predict.py`, and the training object.

## Normalization range

The repo uses the same image scale in both training and inference helpers:

- source pixels are mapped from `[0, 255]` to `[-1, 1]`
- generated tensors are denormalized back to `[0, 1]` with `denorm(x) = x * 0.5 + 0.5`
- visualization steps then convert to uint8 images as needed

This is the range to use when building synthetic tensors for model checks.

## Utility function map

| Function | Input | Output | Notes |
| --- | --- | --- | --- |
| `preprocessing(x)` | numeric array | normalized array in `[-1, 1]` | applies `x / 127.5 - 1` |
| `denorm(x)` | tensor in `[-1, 1]` | tensor in `[0, 1]` | used before visualization |
| `tensor2numpy(x)` | CHW tensor | HWC numpy array | detaches and moves to CPU |
| `RGB2BGR(x)` | RGB image array | BGR image array | OpenCV channel swap helper |
| `cam(x, size)` | CAM heatmap | colorized heatmap in `[0, 1]` | min-max normalizes and applies JET colormap |
| `load_test_data(image_path, size)` | image path | batch tensor-like numpy array | handles alpha compositing over white, resize, RGB/BGR conversion, and preprocessing |
| `inverse_transform(images)` | normalized image array | `[0, 1]` image array | helper for save paths |
| `merge(images, size)` | batch of images | tiled canvas | legacy visualization helper |
| `check_folder(log_dir)` | path | created path | creates the directory if needed |
| `str2bool(x)` | string | boolean | accepts the repo's CLI flags |

## CAM rendering contract

`cam(x, size)` performs a simple visualization pipeline:

1. shift by the minimum value
2. divide by the maximum value
3. scale to `uint8`
4. resize to the requested size
5. apply OpenCV JET color map
6. divide by `255.0`

This means the function expects a non-flat heatmap. A completely flat array can produce divide-by-zero behavior in ports, so guard that case if you reimplement it.

## Validation checks

A safe utility smoke should confirm:

- `preprocessing` maps 0 to about `-1` and 255 to about `1`
- `denorm` inverts the range for representative values
- `tensor2numpy` returns HWC order
- `cam` returns a three-channel colorized image

## Practical use

Use these helpers in the same way the repo does:

- prepare tensors for the generator in `[-1, 1]`
- denormalize outputs before composing visual grids
- convert channel order explicitly when handing off between tensor and OpenCV code
- keep visualization logic out of training logic unless you are porting the existing helper behavior

