# MODNet matting API reference

This reference records the observable interfaces in the source snapshot. Paths
are relative to the `tensorrt_demos` repository root unless stated otherwise.

## Command-line interfaces

### `modnet/torch2onnx/export.py`

The module is invoked as `python -m torch2onnx.export` from `modnet/`, so the
package directory is importable. Arguments:

| Argument | Default | Meaning |
|---|---:|---|
| `--width INT` | `512` | exported input width |
| `--height INT` | `288` | exported input height |
| `-v`, `--verbose` | false | verbose `torch.onnx.export` logging |
| `input_ckpt` | required | PyTorch checkpoint path |
| `output_onnx` | required | output ONNX path |

The output model has fixed batch 1, input `input`, output `output`, and opset
11. Export uses CUDA and loads `torch.load(input_ckpt)` into the MODNet model.

### `modnet/onnx_to_tensorrt.py`

Invoke from `modnet/`:

```text
usage concept: python onnx_to_tensorrt.py [options] input_onnx output_engine
```

| Argument | Default | Meaning |
|---|---:|---|
| `-v`, `--verbose` | false | TensorRT verbose logger |
| `--int8` | false | parsed but fails: INT8 not implemented |
| `--dla_core INT` | `-1` | parsed but fails when nonnegative |
| `--width INT` | `640` | fixed profile width; must match graph |
| `--height INT` | `480` | fixed profile height; must match graph |
| `input_onnx` | required | ONNX file; checked with `os.path.isfile` |
| `output_engine` | required | serialized engine path |

Implementation details:

- requires major TensorRT version 7 or newer;
- uses explicit batch and forces network batch size 1;
- assumes the first network input is the image input;
- sets min/opt/max profile to the same `(1,3,height,width)`;
- allocates `1 << 30` bytes of workspace;
- enables `GPU_FALLBACK` and `FP16`;
- calls `builder.build_engine(network, config)` and serializes the result.

The source profile name is `Input`, while the exporter writes `input`. Verify
and correct this case mismatch for a graph produced by the included exporter.

### `trt_modnet.py`

The parser combines the camera arguments with:

| Argument | Default | Meaning |
|---|---:|---|
| `--background STR` | empty | `.jpg`/`.png` still, `.mp4`/`.ts` video, or empty black |
| `--create_video STR` | empty | output basename; writer adds `.ts` or `.mp4` |
| `--demo_mode` | false | enable 360-frame blender demonstration |

Camera arguments supplied by `utils.camera.add_camera_args`:

| Argument | Default | Source behavior |
|---|---:|---|
| `--image STR` | none | repeat a still image |
| `--video STR` | none | video file; EOF may loop with `--video_looping` |
| `--video_looping` | false | reopen foreground video at EOF |
| `--rtsp STR` | none | RTSP H.264 stream |
| `--rtsp_latency INT` | 200 | RTSP pipeline latency in milliseconds |
| `--usb INT` | none | USB device id |
| `--gstr STR` | none | formatted GStreamer input string |
| `--onboard INT` | none | Jetson onboard pipeline selector |
| `--copy_frame` | false | copy live capture frame on read |
| `--do_resize` | false | resize image/video file frames |
| `--width INT` | 640 | requested/live/output width |
| `--height INT` | 480 | requested/live/output height |

The parser does not enforce exactly one source. `Camera` chooses in this
precedence order: image, video, RTSP, USB, GStreamer, onboard; with none it
raises `RuntimeError('no camera type specified!')`.

## `utils.modnet`

### `_preprocess_modnet(img, input_shape)`

- Input: BGR NumPy array, normally `uint8`, shape `(source_H, source_W, 3)`;
  `input_shape` is `(engine_H, engine_W)`.
- Resize: `(engine_W, engine_H)`, `cv2.INTER_AREA`.
- Color/layout: BGR→RGB, HWC→CHW.
- Type/normalization: `float32`; `(pixel - 127.5) / 127.5`.
- Return: `(3, engine_H, engine_W)` contiguousness is established by the caller.

### `_postprocess_modnet(output, output_shape)`

- Input: output matte array and `(source_H, source_W)`.
- Resizes with `cv2.INTER_AREA` to `(source_W, source_H)`.
- Return: 2-D matte at source frame dimensions.

### `TrtMODNet(cuda_ctx=None)`

Construction initializes TensorRT plugins, loads `modnet/modnet.engine`, creates
an execution context and CUDA stream, and allocates host/device buffers. A
provided PyCUDA context is pushed during resource setup and each inference;
it is popped afterward. A failure allocating resources becomes
`RuntimeError('fail to allocate CUDA resources')`.

Required engine contract:

```text
bindings: exactly ['input', 'output']
input:  FLOAT, [1, 3, engine_H, engine_W]
output: FLOAT, [1, 1, engine_H, engine_W]
```

### `TrtMODNet.infer(img)`

Preprocesses the source BGR image, calls `execute_async_v2`, reshapes the first
output to the engine output spatial shape, and returns a resized 2-D matte.
The intended blend domain is float values from 0 to 1. The function does not
clip, threshold, or convert to 8-bit.

### `allocate_buffers(engine, context)`

Allocates one pagelocked host buffer and one CUDA device buffer for each of
input/output. It asserts exactly two bindings, float-compatible input/output,
input batch/channel `(1,3)`, and equal input/output spatial dimensions.

### `do_inference_v2(context, bindings, inputs, outputs, stream)`

Copies all inputs host→device asynchronously, calls
`context.execute_async_v2(bindings=..., stream_handle=...)`, copies outputs
device→host asynchronously, synchronizes the stream, and returns host arrays.

## `trt_modnet` orchestration classes

### `BackgroundBlender(demo_mode=False)`

`blend(img, bg, matte)` computes:

```python
(img * matte[..., np.newaxis] + bg * (1 - matte[..., np.newaxis])).astype(np.uint8)
```

If demo mode is enabled, `_mod_for_demo` mutates the supplied `bg` and `matte`
according to the frame counter before blending. The counter wraps modulo 360.

### `TrtMODNetRunner(modnet, cam, bggen, blender, writer=None)`

Creates a window sized to `cam.img_width`/`cam.img_height`. Its `run()` loop:
reads foreground/background, exits on a missing foreground frame, infers and
blends, overlays FPS, optionally writes, and displays. Keyboard controls:
`F`/`f` toggles fullscreen and ESC exits.

## `utils.background.Background`

Constructor: `Background(src, width, height, demo_mode=False)`. The
`demo_mode` parameter is stored but not used by `read()`; demo behavior belongs
to `BackgroundBlender`.

- falsey `src`: black `uint8` array `(height,width,3)`;
- lowercase `.jpg` or `.png`: read and resize once, repeat copies;
- lowercase `.mp4` or `.ts`: `cv2.VideoCapture`, resize each frame, reopen at
  EOF to loop;
- any other type/suffix: `ValueError`.

For image input, a failed `cv2.imread` triggers an assertion. For video input,
construction asserts `cap.isOpened()`.

## `utils.camera.Camera`

Constructor: `Camera(args)` where `args` contains all fields added by
`add_camera_args`. It opens one source, stores `img_width` and `img_height`,
and for RTSP/USB/onboard sources starts a background grab thread. `read()`
returns a BGR NumPy frame or `None` on closed/exhausted/error. `release()` stops
the thread, tries to release the capture, and marks the camera closed.

Source specifics:

- file image: `cv2.imread`; with `--do_resize`, resize once;
- file video: synchronous `VideoCapture`; optional EOF reopen;
- RTSP: GStreamer with `omxh264dec` or `avdec_h264` if discoverable;
- USB: GStreamer `v4l2src` when `USB_GSTREAMER=True`, otherwise OpenCV;
- custom GStreamer: calls `.format(width=...,height=...)` on the supplied text;
- onboard: selects legacy `nvcamerasrc` or `nvarguscamerasrc` pipeline.

## `utils.writer.get_video_writer`

`get_video_writer(name, width, height, fps=30)` checks GStreamer plugin text for
`omxh264dec`. If present, returns a GStreamer H.264 MPEG-TS writer and uses
`name + '.ts'`; otherwise returns an OpenCV `mp4v` writer using `name + '.mp4'`.
The source does not normalize a supplied extension or check `isOpened()`.

## `modnet.test_onnx` and `test_modnet`

`modnet/test_onnx.py` is a GUI, CPU ONNX Runtime smoke test as described in
`workflows.md`. It uses the graph's discovered input/output names.

Root `test_modnet.py` is a CUDA/TensorRT smoke test. It imports
`pycuda.autoinit`, loads `modnet/image.jpg`, constructs `TrtMODNet`, calls
`infer`, and displays the matte in an OpenCV window. It does not parse CLI
arguments, save output, or perform numeric assertions.
