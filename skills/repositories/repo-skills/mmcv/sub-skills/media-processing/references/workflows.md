# Media Workflows

These recipes assume `import mmcv` and `import numpy as np`. They avoid original MMCV repo files and work with caller-provided paths, bytes, arrays, or temporary files.

## Zero-Network Image Preprocessing From Bytes

Use this when an agent receives image bytes and must prepare model-ready data while keeping color and shape conventions explicit.

```python
content = image_bytes  # bytes from an upload, database, or local read
img_bgr = mmcv.imfrombytes(content, flag='color', channel_order='bgr')
assert img_bgr.ndim == 3 and img_bgr.shape[2] == 3

resized_bgr, w_scale, h_scale = mmcv.imresize(
    img_bgr, (320, 192), return_scale=True, interpolation='bilinear')
assert resized_bgr.shape[:2] == (192, 320)

mean = np.array([123.675, 116.28, 103.53], dtype=np.float32)
std = np.array([58.395, 57.12, 57.375], dtype=np.float32)
normalized_rgb = mmcv.imnormalize(resized_bgr, mean, std, to_rgb=True)
assert normalized_rgb.dtype == np.float32

preview_bgr = mmcv.imdenormalize(normalized_rgb, mean, std, to_bgr=True)
preview_bgr = np.clip(preview_bgr, 0, 255).astype(np.uint8)
mmcv.imwrite(preview_bgr, preview_path)
```

Key checks:

- `imresize(..., (320, 192))` means width `320`, height `192`; validate with `shape[:2] == (192, 320)`.
- `imnormalize(..., to_rgb=True)` converts BGR input to RGB before normalization; use `to_rgb=False` if the input is already RGB or the model expects BGR statistics.
- Preview writing expects a BGR-like array for normal OpenCV-style image colors.

## Backend Selection for Local Image IO

Use default `cv2` for broad behavior. Switch only when a requirement justifies it.

```python
try:
    mmcv.use_backend('pillow')
    img = mmcv.imread(path, channel_order='rgb', backend='pillow')
finally:
    mmcv.use_backend('cv2')
```

Guidelines:

- `backend='pillow'` is useful for Pillow-specific EXIF/mode handling but requires Pillow and `uint8` for Pillow-backed resize/photometric operations.
- `backend='turbojpeg'` requires `PyTurboJPEG` and is JPEG-focused.
- `backend='tifffile'` requires `tifffile` and is for TIFF-like data.
- For remote or custom storage, prefer `backend_args` on `imread`/`imwrite` instead of deprecated `file_client_args`.

## Color Conversion and Grayscale Handling

```python
img_bgr = mmcv.imread(path)  # default BGR
gray_2d = mmcv.bgr2gray(img_bgr)
gray_3d = mmcv.bgr2gray(img_bgr, keepdim=True)
img_rgb = mmcv.bgr2rgb(img_bgr)
img_bgr_again = mmcv.rgb2bgr(img_rgb)
```

Use `keepdim=True` if downstream code expects `H,W,1`. Use `gray2bgr` or `gray2rgb` before APIs that require 3 channels.

## Geometric Preprocessing Without Pipeline Classes

Functional utilities are owned here. If a task asks for `Resize`, `Compose`, or data loading pipeline transforms, route to `../data-transforms/`.

```python
img = mmcv.imread(path)
scaled, scale = mmcv.imrescale(img, (1333, 800), return_scale=True)
multiple = mmcv.imresize_to_multiple(scaled, divisor=32, scale_factor=1.0)
padded = mmcv.impad(multiple, shape=(832, 1344), pad_val=(114, 114, 114))
flipped = mmcv.imflip(padded, direction='horizontal')
rotated = mmcv.imrotate(flipped, angle=15, auto_bound=True, border_value=0)
```

Remember:

- `imrescale` preserves aspect ratio and returns one scalar scale factor.
- `impad(shape=(height, width))` differs from `imresize(size=(width, height))`.
- `imcrop` boxes are `(x1, y1, x2, y2)` and return type changes between single and multiple boxes.

## Photometric Adjustments

```python
img = mmcv.imread(path)
bright = mmcv.adjust_brightness(img, factor=1.2)
contrast = mmcv.adjust_contrast(bright, factor=0.9)
sharp = mmcv.adjust_sharpness(contrast, factor=1.5)
hue = mmcv.adjust_hue(sharp, hue_factor=0.1)
```

For deterministic reproducibility, avoid or seed callers around random helpers such as `adjust_lighting` and `cutout`. Clip/cast outputs before writing when working with float arrays.

## Tensor to Images

```python
# tensor shape: N, C, H, W
imgs = mmcv.tensor2imgs(tensor, mean=(123.675, 116.28, 103.53), std=(58.395, 57.12, 57.375), to_rgb=True)
for img in imgs:
    assert img.flags['C_CONTIGUOUS']
    assert img.dtype == np.uint8
```

This requires PyTorch. For one-channel tensors, pass one-element `mean`/`std` and `to_rgb=False`.

## Headless Bounding-Box Visualization

Avoid GUI windows in CI, containers, SSH, and servers.

```python
img = mmcv.imread(path)
bboxes = np.array([[10, 12, 80, 96], [100, 40, 160, 120]], dtype=np.float32)
drawn = mmcv.imshow_bboxes(
    img, bboxes, colors='green', thickness=2, show=False, out_file=out_path)
assert drawn.shape == img.shape
```

For detections:

```python
bboxes = np.array([[10, 12, 80, 96, 0.93], [100, 40, 160, 120, 0.41]], dtype=np.float32)
labels = np.array([0, 1], dtype=np.int64)
drawn = mmcv.imshow_det_bboxes(
    img, bboxes, labels, class_names=['cat', 'dog'], score_thr=0.5,
    bbox_color='yellow', text_color='white', show=False, out_file=out_path)
```

Colors are BGR. `mmcv.color_val('blue')` returns `(255, 0, 0)`.

## Video Reading and Frame Export

```python
with mmcv.VideoReader(video_path, cache_capacity=20) as reader:
    assert reader.opened
    first = reader[0]
    last = reader[-1]
    sample = reader[5:10]
    for frame in sample:
        assert frame is None or frame.ndim == 3
    reader.cvt2frames(frame_dir, start=0, max_num=10, show_progress=False)
```

Notes:

- Frames are BGR arrays from OpenCV.
- `len(reader)` uses metadata; some codecs report imperfect frame counts.
- If random seeks behave oddly, prefer sequential iteration or re-open the reader.

## Frames to Video and ffmpeg Editing

```python
mmcv.frames2video(frame_dir, out_video, fps=12, fourcc='XVID', show_progress=False)
```

Use ffmpeg wrappers only when the `ffmpeg` executable is available:

```python
mmcv.resize_video(in_video, resized_video, size=(640, 360), keep_ar=True, log_level='warning')
mmcv.cut_video(resized_video, clip_video, start=3.0, end=8.0, log_level='warning')
mmcv.concat_video([clip_a, clip_b], joined_video, log_level='warning')
```

Keep file paths simple and trusted because `convert_video` builds a shell command string.

## Dense Flow IO, Quantization, and Visualization

```python
flow = np.zeros((64, 96, 2), dtype=np.float32)
flow[..., 0] = 1.0  # horizontal displacement dx
flow[..., 1] = -0.5 # vertical displacement dy

mmcv.flowwrite(flow, flow_path)
loaded = mmcv.flowread(flow_path)
assert loaded.shape == flow.shape

mmcv.flowwrite(flow, quantized_path, quantize=True, concat_axis=1, max_val=0.05, norm=True)
loaded_q = mmcv.flowread(quantized_path, quantize=True, concat_axis=1, max_val=0.05, denorm=True)
assert loaded_q.shape == flow.shape

rgb_float = mmcv.flow2rgb(loaded_q)
preview_bgr = np.clip(rgb_float[..., ::-1] * 255, 0, 255).astype(np.uint8)
mmcv.imwrite(preview_bgr, flow_preview_path)
```

Avoid `mmcv.flowshow()` in headless environments; it calls OpenCV GUI display. Use `flow2rgb` and save an image instead.

## Flow From Bytes and Sparse KITTI Flow

```python
flow = mmcv.flow_from_bytes(dense_flo_bytes)
assert flow.ndim == 3 and flow.shape[-1] == 2

sparse_flow, valid = mmcv.sparse_flow_from_bytes(kitti_png_bytes)
assert sparse_flow.shape[:2] == valid.shape
assert sparse_flow.shape[-1] == 2
```

Dense bytes must be `.flo`-style with `PIEH` header. Sparse bytes must be KITTI-style 16-bit PNG bytes.

## Flow Warping Prototype

```python
warped = mmcv.flow_warp(img_bgr, flow, filling_value=0, interpolate_mode='bilinear')
assert warped.shape == img_bgr.shape
```

`flow_warp` is useful for prototyping but warns that it is not computationally optimized. Route compiled acceleration questions to `../ops-and-builds/`.

## Scalar Array Quantization

```python
arr = np.linspace(-2.0, 2.0, 9, dtype=np.float32).reshape(3, 3)
q = mmcv.quantize(arr, min_val=-1.0, max_val=1.0, levels=1000, dtype=np.uint16)
recovered = mmcv.dequantize(q, min_val=-1.0, max_val=1.0, levels=1000, dtype=np.float32)
```

Use this for compact approximate storage or bucketing, not exact round-tripping. Values outside the range are clipped before binning.
