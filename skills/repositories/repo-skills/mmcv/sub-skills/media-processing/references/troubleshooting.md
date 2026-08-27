# Media Troubleshooting

## Image IO and Backend Failures

| Symptom | Likely Cause | Recovery |
| --- | --- | --- |
| `ImportError: PyTurboJPEG/Pillow/tifffile is not installed` after `use_backend(...)` | Optional image backend is not installed. | Use `backend='cv2'` or install the optional package. Do not assume all supported backends are present in `mmcv-lite`. |
| `ValueError: backend: ... is not supported` | Typo or using decode-only backend for resize/photometric helper. | Decode backends are `cv2`, `pillow`, `turbojpeg`, `tifffile`; resize/photometric backends are `cv2` or `pillow`. |
| Image colors look swapped red/blue | MMCV defaults to BGR, but downstream expects RGB. | Use `imread(..., channel_order='rgb')`, `imfrombytes(..., channel_order='rgb')`, or `mmcv.bgr2rgb(img)`. When writing OpenCV-style previews, convert RGB back to BGR. |
| `TypeError: "img" must be a numpy array or a str or a pathlib.Path object` | Passed bytes to `imread`, or another unsupported object. | Use `imfrombytes(content)` for bytes. Use `imread(path_or_array)` only for paths/arrays. |
| Decoded image is `None` or write returns `False` | Invalid bytes, unsupported suffix, missing codec, or backend could not decode/encode. | Verify non-empty bytes/path, choose a common suffix such as `.png` or `.jpg`, and try `backend='cv2'` or `backend='pillow'`. |
| Warning about `file_client_args` deprecation | Old MMCV 1.x style storage arguments. | Use `backend_args` and never pass both `file_client_args` and `backend_args`. |

## Shape, Size, and Coordinate Confusion

| Symptom | Likely Cause | Recovery |
| --- | --- | --- |
| Resized output shape appears reversed | `imresize(size)` takes `(width, height)`, but array shape reports `(height, width, channels)`. | For output `H=192, W=320`, call `imresize(img, (320, 192))` and assert `out.shape[:2] == (192, 320)`. |
| Padding target gives unexpected dimensions | `impad(shape)` takes `(height, width)`, unlike `imresize(size)`. | Use `impad(img, shape=(target_h, target_w))`; use four-value `padding=(left, top, right, bottom)` for borders. |
| Crops are one pixel larger than expected | `imcrop` treats `(x1, y1, x2, y2)` as inclusive coordinates. | Subtract one from exclusive max coordinates before calling `imcrop`, or accept `x2-x1+1` and `y2-y1+1` output. |
| Single crop returns array but multiple crops return list | `imcrop` return type depends on `bboxes.ndim`. | Normalize with `patches = [patch] if patch.ndim == img.ndim else patch` or always pass `bboxes` as `N,4` and expect a list. |
| Rotation with custom center and `auto_bound=True` fails | `imrotate` forbids combining custom `center` with `auto_bound`. | Choose either a custom center with original canvas size or `auto_bound=True` with default center. |

## Dtype and Range Surprises

| Symptom | Likely Cause | Recovery |
| --- | --- | --- |
| `AssertionError` in `imnormalize_` or `imdenormalize` | In-place normalization helpers reject `uint8`. | Use `imnormalize` for a copying cast to `float32`, or cast manually before `imnormalize_`. |
| Normalized preview writes as black/white/noisy | Writing normalized float data directly. | Reverse with `imdenormalize`, then `np.clip(..., 0, 255).astype(np.uint8)` before `imwrite`. |
| YCbCr helpers raise dtype errors | `rgb2ycbcr`/`bgr2ycbcr` accept only `uint8` `[0,255]` or `float32` `[0,1]`. | Convert range and dtype intentionally before calling. |
| Pillow-backed resize/adjustment asserts on dtype | Pillow backend only supports `uint8` for those paths. | Use `backend='cv2'` for float arrays or cast/clip to `uint8` first. |
| Array quantization is not exact after dequantization | `dequantize` returns bin centers and quantize clips out-of-range values. | Treat it as approximate compression/bucketing. Increase `levels` or preserve originals when exact values matter. |

## Visualization and Headless Environments

| Symptom | Likely Cause | Recovery |
| --- | --- | --- |
| OpenCV GUI error, hang, or no display from `imshow`/`flowshow` | Running in headless container, CI, SSH, or no `$DISPLAY`. | Avoid GUI calls. Use `imshow_bboxes(..., show=False, out_file=...)`, return arrays, or save `flow2rgb` output via `imwrite`. |
| Detection visualization raises shape assertions | `bboxes`/`labels` shapes mismatch or scores missing with `score_thr`. | Use `bboxes.shape == (N,4)` or `(N,5)`, `labels.shape == (N,)`; if `score_thr > 0`, provide score column. |
| Box/text colors are wrong | `color_val` and visualization colors are BGR. | Use MMCV color names or BGR tuples. `color_val('blue') == (255,0,0)`. |
| `color_val` rejects a color | Unsupported input type or out-of-range channel. | Use `mmcv.Color`, enum string, 3-tuple, int in `[0,255]`, or one-dimensional 3-value `np.ndarray`. |

## Video and Codec Issues

| Symptom | Likely Cause | Recovery |
| --- | --- | --- |
| `Video file not found` | Local path does not exist; only HTTP(S) bypasses local existence check. | Verify the path, mount, or use a valid URL. |
| `reader.opened` is false or frame reads return `None` early | Codec unsupported by OpenCV build or corrupt file. | Try a common codec/container, re-encode with ffmpeg, or inspect with external media tooling. |
| `frames2video` fails at first frame | Missing `filename_tmpl.format(start)` or nonmatching extension. | Ensure frames are named like `000000.jpg` by default, or pass matching `filename_tmpl`, `start`, and `end`. |
| ffmpeg wrappers do nothing or raise executable errors | `ffmpeg` executable missing or not on PATH. | Install/activate ffmpeg or use OpenCV-only `VideoReader`/`frames2video` paths. |
| ffmpeg output has no audio/video or concat fails | Codec/container mismatch, stream-copy limitations, or incompatible input files. | Set explicit `vcodec`/`acodec`, re-encode inputs to a common format, and lower `log_level` only after debugging. |
| Shell-sensitive file path breaks `convert_video` | MMCV builds an ffmpeg shell command string. | Prefer trusted simple paths without shell metacharacters; do not pass untrusted user path fragments into ffmpeg kwargs. |

## Optical Flow Failures

| Symptom | Likely Cause | Recovery |
| --- | --- | --- |
| `ValueError: Invalid flow with shape ...` | Flow array is not `H,W,2`. | Reshape or stack `dx` and `dy` as `np.dstack((dx, dy))`; validate `flow.ndim == 3 and flow.shape[-1] == 2`. |
| `.flo` read says header does not contain `PIEH` | File is not Middlebury `.flo` dense flow. | Use the correct file, pass `quantize=True` for MMCV quantized image flow, or parse another format separately. |
| Quantized flow read has wrong shape | `concat_axis` used on read does not match write, or image dimensions are not divisible by two on that axis. | Track whether `flowwrite(..., concat_axis=0)` stacked vertically or `concat_axis=1` stacked horizontally and use the same value in `flowread`. |
| Dequantized flow magnitude is unexpectedly small/large | Mismatch between `norm` and `denorm` settings or `max_val`. | If `quantize_flow(..., norm=True)`, read with `denorm=True`. Use the same `max_val` for quantize/dequantize. |
| `flow_warp` is slow or warns | Function is a Python prototype, not optimized. | Use it for small debugging/prototyping. Route compiled acceleration or ops-build questions to `../ops-and-builds/`. |
| Flow visualization hides large/NaN values | `flow2rgb` zeroes NaN/inf or components over `unknown_thr`. | Clean flow values or raise `unknown_thr` when appropriate; inspect masks before visualization. |
| `sparse_flow_from_bytes` output seems channel-swapped | KITTI PNG stores encoded components; MMCV reverses OpenCV BGR order internally. | Trust returned `(flow, valid)` shapes, and validate against KITTI encoding assumptions before custom decoding. |

## Routing Mistakes

| Symptom | Likely Cause | Recovery |
| --- | --- | --- |
| Task asks for `Resize`, `Compose`, `LoadImageFromFile`, or transform config pipelines | These are pipeline/data-transform classes, not media functional APIs. | Route to `../data-transforms/`. |
| Task asks why `import mmcv.ops` fails with `_ext` missing | Installed distribution is `mmcv-lite` or full ops were not built. | Route to `../ops-and-builds/`; media APIs here do not require compiled ops. |
| Task asks for convolution/norm/activation/layer builders | CNN model-building surface, not media processing. | Route to `../cnn-model-building/`. |
