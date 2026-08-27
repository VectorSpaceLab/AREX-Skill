# Media API Reference

This reference targets MMCV 2.2.0 media utilities imported from `mmcv`. The checkout may install as `mmcv-lite` while still importing as `mmcv`; compiled `mmcv.ops` is not required for the APIs below.

## Image IO and Backends

| API | Use | Gotchas |
| --- | --- | --- |
| `mmcv.use_backend(backend)` | Sets global image decode/resize backend. Supported decode backends: `cv2`, `pillow`, `turbojpeg`, `tifffile`. | Raises `ImportError` if optional backend is missing. `turbojpeg` supports only JPEG `color`/`grayscale`; resize supports only `cv2`/`pillow`. |
| `mmcv.imread(img_or_path, flag='color', channel_order='bgr', backend=None, backend_args=None)` | Read local/remote image paths or return an input `np.ndarray` unchanged. | Default color output is BGR. `flag` supports `color`, `grayscale`, `unchanged`, `color_ignore_orientation`, `grayscale_ignore_orientation`. Do not pass deprecated `file_client_args` together with `backend_args`. |
| `mmcv.imfrombytes(content, flag='color', channel_order='bgr', backend=None)` | Decode image bytes. | `content` must be bytes, not a path string. `backend=None` uses the current global backend. |
| `mmcv.imwrite(img, file_path, params=None, auto_mkdir=None, backend_args=None)` | Encode by filename suffix and write through mmengine file IO. | Returns boolean encode success. `auto_mkdir` is deprecated; modern file backends create parent dirs. Image channel order is not converted before writing. |

## Image Color and Geometry

| API | Use | Gotchas |
| --- | --- | --- |
| `mmcv.bgr2rgb(img)`, `mmcv.rgb2bgr(img)` | Swap first and third channels. | Useful after `imread(..., channel_order='bgr')` before RGB model/display code. |
| `mmcv.bgr2gray(img, keepdim=False)`, `mmcv.rgb2gray(img, keepdim=False)` | Convert 3-channel image to grayscale. | `keepdim=True` returns `H, W, 1`; otherwise `H, W`. |
| `mmcv.gray2bgr(img)`, `mmcv.gray2rgb(img)` | Expand grayscale to 3 channels. | Accepts `H, W` or `H, W, 1`. |
| `mmcv.bgr2hsv`, `mmcv.hsv2bgr`, `mmcv.bgr2hls`, `mmcv.hls2bgr` | OpenCV color conversions. | Inputs are OpenCV-style BGR unless the name says RGB. |
| `mmcv.rgb2ycbcr(img, y_only=False)`, `mmcv.bgr2ycbcr(...)`, `mmcv.ycbcr2rgb(...)`, `mmcv.ycbcr2bgr(...)` | Matlab-compatible BT.601 YCbCr conversions. | Accept only `np.uint8` range `[0,255]` or `np.float32` range `[0,1]`; preserve dtype/range. |
| `mmcv.imconvert(img, src, dst)` | Dynamic OpenCV colorspace conversion such as `src='bgr', dst='rgb'`. | Requires a matching `cv2.COLOR_<SRC>2<DST>` constant. |
| `mmcv.imresize(img, size, return_scale=False, interpolation='bilinear', out=None, backend=None)` | Resize to exact target `size`. | `size` is `(width, height)`, but output shape is `(height, width, channels)`. With `return_scale=True`, returns `(resized, w_scale, h_scale)`. Pillow backend requires `uint8`. |
| `mmcv.imrescale(img, scale, return_scale=False, interpolation='bilinear', backend=None)` | Resize while preserving aspect ratio. | `scale` can be a factor or max-bound tuple; tuple logic fits within long/short edge limits. With `return_scale=True`, returns one scalar scale factor. |
| `mmcv.imresize_to_multiple(img, divisor, size=None, scale_factor=None, keep_ratio=False, return_scale=False, ...)` | Resize by target size or scale factor, then round dimensions up to multiples of `divisor`. | Exactly one of `size` or `scale_factor` is required. `divisor` tuple is `(w_divisor, h_divisor)`. |
| `mmcv.imcrop(img, bboxes, scale=1.0, pad_fill=None)` | Crop one `(x1, y1, x2, y2)` box or an array of boxes. | Coordinates are inclusive. One box returns an array; multiple boxes return a list. `pad_fill` lets out-of-image scaled boxes keep requested size. |
| `mmcv.imflip(img, direction='horizontal')`, `mmcv.imflip_(...)` | Flip horizontal, vertical, or diagonal. | `imflip_` mutates in place. |
| `mmcv.impad(img, shape=None, padding=None, pad_val=0, padding_mode='constant')` | Pad to target shape or with explicit border padding. | Exactly one of `shape` or `padding`. `shape` is `(height, width)`. Four-value `padding` is `(left, top, right, bottom)`. |
| `mmcv.impad_to_multiple(img, divisor, pad_val=0)` | Pad height/width up to multiples of `divisor`. | Uses `impad(shape=(ceil_h, ceil_w))`. |
| `mmcv.imrotate(img, angle, center=None, scale=1.0, border_value=0, interpolation='bilinear', auto_bound=False, border_mode='constant')` | Rotate clockwise for positive angles. | `center` is `(width_coord, height_coord)`; cannot combine `center` with `auto_bound=True`. |
| `mmcv.cutout`, `mmcv.imshear`, `mmcv.imtranslate` | Additional geometric augmentation helpers. | Random or augmentation-oriented; prefer deterministic calls when reproducibility matters. |

## Image Photometric and Tensor Helpers

| API | Use | Gotchas |
| --- | --- | --- |
| `mmcv.imnormalize(img, mean, std, to_rgb=True)` | Copy image to `float32`, optionally convert BGR to RGB, then `(img - mean) / std`. | Default assumes input is BGR and model expects RGB normalization. |
| `mmcv.imnormalize_(img, mean, std, to_rgb=True)` | In-place normalization. | Input must not be `uint8`; cast to `float32` first. |
| `mmcv.imdenormalize(img, mean, std, to_bgr=True)` | Reverse normalization, optionally RGB back to BGR. | Input must not be `uint8`; output dtype follows OpenCV arithmetic, typically float. |
| `mmcv.iminvert`, `mmcv.solarize`, `mmcv.posterize` | Simple pixel intensity transformations. | Expect image-like numeric arrays; `posterize(bits)` reduces per-channel bit depth. |
| `mmcv.adjust_color`, `mmcv.adjust_brightness`, `mmcv.adjust_contrast`, `mmcv.adjust_sharpness`, `mmcv.adjust_hue` | Enhancement helpers with OpenCV/Pillow backends. | Pillow backend requires `uint8` and internally treats arrays as BGR-to-RGB-to-BGR. `adjust_hue` requires `hue_factor` in `[-0.5, 0.5]`. |
| `mmcv.imequalize`, `mmcv.auto_contrast`, `mmcv.clahe`, `mmcv.lut_transform`, `mmcv.adjust_lighting` | Histogram/LUT/PCA lighting helpers. | `clahe` requires a 2D grayscale image. `lut_transform` requires values in `[0,255]` and a `(256,)` LUT. `adjust_lighting` is random. |
| `mmcv.tensor2imgs(tensor, mean=None, std=None, to_rgb=True)` | Convert `N,C,H,W` PyTorch tensor to list of contiguous `uint8` images. | Requires PyTorch. `C` must be 1 or 3; one-channel tensors require `to_rgb=False`. |

## Video and Optical Flow

| API | Use | Gotchas |
| --- | --- | --- |
| `mmcv.VideoReader(filename, cache_capacity=10)` | Sequence-like video reader backed by OpenCV. | Local files are checked before opening; HTTP(S) URLs are allowed. Frames are BGR arrays. Properties include `width`, `height`, `resolution`, `fps`, `frame_cnt`, `fourcc`, `position`, `opened`. |
| `reader.read()`, `reader.get_frame(i)`, `reader[i]`, `reader[start:stop]`, iteration | Read frames with cache and accurate seek handling. | `read()` returns `None` at end. Negative indexing is supported. Out-of-range raises `IndexError`. Use context manager to release capture. |
| `reader.cvt2frames(frame_dir, file_start=0, filename_tmpl='{:06d}.jpg', start=0, max_num=0, show_progress=True)` | Dump frames to image files. | Raises if `start` is beyond total frames. Set `show_progress=False` in non-interactive logs. |
| `mmcv.frames2video(frame_dir, video_file, fps=30, fourcc='XVID', filename_tmpl='{:06d}.jpg', start=0, end=0, show_progress=True)` | Join numbered frames into a video. | Reads frame `start` to infer resolution. `end=0` counts files matching the extension. Codec/container support depends on OpenCV build. |
| `mmcv.convert_video(in_file, out_file, print_cmd=False, pre_options='', **kwargs)` | General ffmpeg wrapper. | Requires `ffmpeg` executable. Keyword options become CLI flags; `log_level` maps to `-loglevel`. Paths with special shell characters are risky because the wrapper builds a shell string. |
| `mmcv.resize_video(in_file, out_file, size=None, ratio=None, keep_ar=False, log_level='info', print_cmd=False)` | ffmpeg resize by exact `(width,height)` or ratio. | Exactly one of `size` or `ratio` is required. `keep_ar=True` uses ffmpeg `force_original_aspect_ratio=decrease`. |
| `mmcv.cut_video(in_file, out_file, start=None, end=None, vcodec=None, acodec=None, log_level='info', print_cmd=False)` | ffmpeg clip extraction. | Defaults to stream copy when codecs are `None`; `end` becomes duration `end - start`. |
| `mmcv.concat_video(video_list, out_file, vcodec=None, acodec=None, log_level='info', print_cmd=False)` | ffmpeg concat-list wrapper. | Uses a temporary concat file with absolute paths and `-safe 0`; codec compatibility still matters. |
| `mmcv.flowread(flow_or_path, quantize=False, concat_axis=0, **kwargs)` | Read dense `.flo`, quantized image flow, or return flow array unchanged. | Flow arrays must be `H,W,2`. Uncompressed files must have `PIEH` header. Quantized files are split along axis `0` or `1`. |
| `mmcv.flowwrite(flow, filename, quantize=False, concat_axis=0, **kwargs)` | Write uncompressed `.flo` or quantized image flow. | Quantized output is lossy; `concat_axis=0` stacks `dx` above `dy`, `concat_axis=1` stacks side-by-side. |
| `mmcv.quantize_flow(flow, max_val=0.02, norm=True)` | Convert `H,W,2` float flow into uint8 `dx, dy`. | With `norm=True`, `dx` is divided by width and `dy` by height before quantization; values are clipped to `[-max_val, max_val]`. |
| `mmcv.dequantize_flow(dx, dy, max_val=0.02, denorm=True)` | Recover float flow from quantized components. | `dx` and `dy` shapes must match. With `denorm=True`, `dx` is multiplied by width and `dy` by height. |
| `mmcv.flow_warp(img, flow, filling_value=0, interpolate_mode='nearest')` | Prototype image warp with `nearest` or `bilinear`. | Emits a warning and is not optimized. Requires 3D flow and a 3-channel image. |
| `mmcv.flow_from_bytes(content)` | Decode dense `.flo` bytes. | Requires `PIEH` header; returns `H,W,2` float array. |
| `mmcv.sparse_flow_from_bytes(content)` | Decode KITTI-style sparse flow PNG bytes. | Returns `(flow, valid)` where `flow` is `H,W,2` and `valid` is `H,W`. |

## Visualization

| API | Use | Gotchas |
| --- | --- | --- |
| `mmcv.Color` | Enum values `red`, `green`, `blue`, `cyan`, `yellow`, `magenta`, `white`, `black`. | Enum values are BGR tuples, not RGB. |
| `mmcv.color_val(color)` | Normalize color input from enum, name, tuple, int, or `np.ndarray`. | String names index the enum exactly. Tuples/arrays must be 3 channels in `[0,255]`; int returns grayscale tuple. |
| `mmcv.imshow(img, win_name='', wait_time=0)` | Show image in an OpenCV window. | Avoid in headless CI/servers. `wait_time=0` loops until the window is closed or a key is pressed. |
| `mmcv.imshow_bboxes(img, bboxes, colors='green', top_k=-1, thickness=1, show=True, win_name='', wait_time=0, out_file=None)` | Draw one or more bbox arrays on an image. | Set `show=False` and/or `out_file` in headless environments. Coordinates are `(x1,y1,x2,y2)` and colors are BGR. |
| `mmcv.imshow_det_bboxes(img, bboxes, labels, class_names=None, score_thr=0, bbox_color='green', text_color='green', thickness=1, font_scale=0.5, show=True, win_name='', wait_time=0, out_file=None)` | Draw detections with labels/scores. | `bboxes` must be `N,4` or `N,5`; `labels` must be `N`. `score_thr>0` requires scores in column 5. |
| `mmcv.flow2rgb(flow, color_wheel=None, unknown_thr=1e6)` | Convert flow array to RGB float visualization in `[0,1]`. | Input must be `H,W,2`. NaN/inf or values above threshold are zeroed. |
| `mmcv.flowshow(flow, win_name='', wait_time=0)` | Show flow using `flow2rgb` and OpenCV display. | Prefer `flow2rgb` plus `mmcv.imwrite((rgb[..., ::-1] * 255).astype('uint8'), path)` for headless use. |

## Array Quantization

| API | Use | Gotchas |
| --- | --- | --- |
| `mmcv.quantize(arr, min_val, max_val, levels, dtype=np.int64)` | Clip numeric array to `[min_val,max_val]` and map to integer bins `[0, levels-1]`. | `levels` must be integer `>1`; `min_val < max_val`; default dtype is `int64`. |
| `mmcv.dequantize(arr, min_val, max_val, levels, dtype=np.float64)` | Map quantized bins back to bin centers. | Returns midpoint values, so recovery is approximate and clipped extremes become near the min/max bin centers. |
