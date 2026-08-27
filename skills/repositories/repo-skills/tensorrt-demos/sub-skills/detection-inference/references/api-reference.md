# Detection API reference

## Command-line options shared by camera demos

The shared camera argument helper is used by `trt_yolo.py`, `trt_yolo_mjpeg.py`,
`trt_ssd.py`, and `trt_ssd_async.py`.

| Option | Type/default | Contract |
|---|---|---|
| `--image FILE` | string / `None` | Image file; read as BGR and repeated as a copied frame. |
| `--video FILE` | string / `None` | OpenCV video file. |
| `--video_looping` | flag / false | Reopen the video after EOF. |
| `--rtsp URI` | string / `None` | RTSP H.264 source through a generated GStreamer pipeline. |
| `--rtsp_latency MS` | integer / 200 | GStreamer RTSP latency. |
| `--usb N` | integer / `None` | USB device `/dev/videoN`; historical code uses GStreamer by default. |
| `--gstr STRING` | string / `None` | Custom GStreamer pipeline; `{width}` and `{height}` are formatted. |
| `--onboard N` | integer / `None` | Jetson onboard camera pipeline; the historical implementation does not use N to select a sensor. |
| `--copy_frame` | flag / false | Copy live frames before returning them. |
| `--do_resize` | flag / false | Resize image/video frames to requested dimensions. |
| `--width N` | integer / 640 | Requested width or pipeline width. |
| `--height N` | integer / 480 | Requested height or pipeline height. |

The implementation's precedence when multiple selectors are given is image,
video, RTSP, USB, GStreamer, onboard. Prefer exactly one; the bundled checker
rejects multiple selectors to make accidental precedence impossible.

## `trt_yolo.py`

- `--model MODEL` — required. Help describes YOLOv3/YOLOv4 family and input
  dimension names such as `yolov4-416` or `yolov4-416x256`.
- `--category_num N` — positive integer, default 80.
- `--conf_thresh T` — float, default 0.3; passed into `TrtYOLO.detect`.
- `--letter_box` — flag; enables aspect-preserving resize/padding.

The script checks `yolo/<model>.trt`, opens `Camera`, constructs
`BBoxVisualization` and `TrtYOLO`, then loops until a window close, ESC, or
input failure. `trt_yolo_cv.py` uses `--video FILE`, `--output FILE`,
`--category_num`, `--model`, and `--letter_box`; its confidence is fixed at
0.3 and it writes MP4V at 30 FPS.

## `trt_yolo_mjpeg.py`

It has the YOLO model and letterbox options plus all camera options and:

- `--mjpeg_port N` — integer, default 8080.

Its confidence is fixed at 0.3. It constructs `MjpegServer(port=...)`, sends
annotated frames with `send_img`, and shuts down in `finally`.

## `trt_ssd.py` and `trt_ssd_async.py`

- `--model MODEL` — optional, default `ssd_mobilenet_v1_coco`, constrained to:
  `ssd_mobilenet_v1_coco`, `ssd_mobilenet_v1_egohands`,
  `ssd_mobilenet_v2_coco`, `ssd_mobilenet_v2_egohands`,
  `ssd_inception_v2_coco`, `ssdlite_mobilenet_v2_coco`.
- Camera options are as above.
- The entrypoint confidence is fixed at 0.3 and the detector input shape is
  `(300, 300)`.

The async entrypoint additionally creates a producer thread and condition
variable. Its display wait timeout is 20 seconds (`MAIN_THREAD_TIMEOUT`).

## `TrtYOLO`

Observed constructor:

```python
TrtYOLO(model, category_num=80, letter_box=False, cuda_ctx=None)
```

`model` selects `yolo/<model>.trt`; `category_num` must agree with engine
outputs/classes; `letter_box` selects default preprocessing; `cuda_ctx` is an
optional caller-owned CUDA context that is pushed around resource setup and
inference.

Observed method:

```python
boxes, scores, classes = detector.detect(
    img, conf_th=0.3, letter_box=None)
```

Input is a BGR image array. `boxes` has shape `(N, 4)` and integer corners;
`scores` and `classes` have length N. The method preprocesses, asynchronously
copies to device, invokes TensorRT, synchronizes, filters/NMSes, maps back to
source coordinates, and clips boxes. It may raise on missing plugin, engine,
CUDA allocation, or TensorRT execution.

## `TrtSSD`

Observed constructor and method:

```python
TrtSSD(model, input_shape=(300, 300), cuda_ctx=None)
boxes, confs, classes = detector.detect(img, conf_th=0.3)
```

The constructor loads `ssd/TRT_<model>.bin`, registers TensorRT plugins, and
allocates host/device buffers. `detect` expects a BGR image and returns Python
lists of `(x1, y1, x2, y2)` boxes, confidences, and integer classes. The
postprocessor interprets each output record as seven values: index, class,
confidence, xmin, ymin, xmax, ymax. Coordinates are normalized in engine
output and scaled to the original image.

## `Camera`

`Camera(args)` expects an argparse-like object with all shared camera
attributes. It exposes:

- `isOpened()` — whether the source opened and supplied an initial frame.
- `read()` — BGR frame or `None` at end/error; live frames may be shared unless
  `copy_frame` is true.
- `release()` — stops the grab thread, releases capture, and marks closed.
- `img_width`, `img_height` — observed frame dimensions.

For a file image, `read()` returns `np.copy` of the stored image indefinitely.
For a video, `read()` returns frames and optionally loops. For live sources,
a grab thread continuously updates `img_handle`; `read()` returns the current
slot or a copy.

## Visualization/display/MJPEG

```python
vis = BBoxVisualization(cls_dict)
annotated = vis.draw_bboxes(img, boxes, confs, classes)
annotated = show_fps(annotated, fps)
server = MjpegServer(port=8080)
server.send_img(annotated)
server.shutdown()
```

`draw_bboxes` mutates and returns the image. Labels are class name plus
confidence with two decimals. `MjpegServer` serves `/mjpg` and `/`, encodes
frames as JPEG, uses a global queue of maximum size two, and may drop frames
when full. The historical handler is unauthenticated and binds broadly by
default; treat it as a trusted-network demo, not a production endpoint.
