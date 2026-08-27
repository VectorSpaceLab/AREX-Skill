# Detection workflows

These procedures describe the observed runtime paths for the repository's
YOLOv3/YOLOv4 and UFF SSD demos. Run them from the normal demo runtime so the
relative `yolo/`, `ssd/`, and `plugins/` artifact paths resolve. Do not copy
engines, shared libraries, installers, or model binaries into this skill.

## 1. Preflight and input selection

1. Record the detector (`yolo` or `ssd`), model string, serialized-engine
   location, TensorRT/PyCUDA/OpenCV versions, CUDA device, input mode, input
   dimensions, confidence, and whether letterboxing/copying is enabled.
2. Confirm that exactly one input selector is present. Use the safe checker,
   which validates arguments only:

   ```bash
   python3 scripts/validate-input-mode.py --detector yolo \
     --model yolov4-416 --image /data/dog.jpg
   python3 scripts/validate-input-mode.py --detector ssd \
     --model ssd_mobilenet_v1_coco --video /data/clip.mp4 \
     --video-looping
   ```

3. Check artifacts and devices in the target environment without changing
   them. YOLO needs `yolo/<model>.trt` and the loadable `yolo_layer` plugin;
   SSD needs `ssd/TRT_<model>.bin` and the required TensorRT plugin/runtime.
4. Run a short native parser/dependency smoke check before opening a camera or
   consuming a long video. These imports happen before argparse in the planned
   candidates, so missing PyCUDA/TensorRT/OpenCV is expected to appear even for
   `--help`:

   ```bash
   python3 trt_yolo.py --help
   python3 trt_ssd.py --help
   ```

   Preserve stderr and classify a failure instead of treating it as a model
   or input failure.

## 2. Interactive YOLO image/video/live inference

Use `trt_yolo.py` for an OpenCV window, FPS overlay, and keyboard controls.
Examples of valid input forms:

```bash
python3 trt_yolo.py --model yolov4-416 --image /data/dog.jpg
python3 trt_yolo.py --model yolov3-416 --video /data/clip.mp4 \
  --video-looping --copy_frame
python3 trt_yolo.py --model yolov4-416 --rtsp \
  rtsp://user:password@camera/live.sdp --rtsp_latency 200 \
  --width 1280 --height 720 --copy_frame
python3 trt_yolo.py --model yolov4-416 --usb 0 \
  --width 1280 --height 720 --copy_frame
python3 trt_yolo.py --model yolov4-416 --gstr \
  'v4l2src device=/dev/video0 ! video/x-raw, width=(int){width}, height=(int){height} ! videoconvert ! appsink' \
  --copy_frame
python3 trt_yolo.py --model yolov4-416 --onboard 0 \
  --width 1280 --height 720 --copy_frame
```

Add `--conf_thresh 0.5` to suppress lower-scoring detections, or
`--category_num N` for an engine trained with N classes. Add `--letter_box`
only when the engine's preprocessing convention requires aspect-ratio
preservation. Press ESC to stop; press F to toggle fullscreen.

The image source is read as a copy and repeats indefinitely. Video ends when
its read returns no frame unless `--video_looping` is set. RTSP, USB, custom
GStreamer, and onboard modes are live sources backed by the camera grab thread;
`--copy_frame` prevents visualization's in-place drawing from changing the
shared frame used by the next inference.

## 3. Interactive UFF SSD inference

Use `trt_ssd.py` with its fixed 300x300 model input and one of its explicit
model choices:

```bash
python3 trt_ssd.py --model ssd_mobilenet_v1_coco --image /data/huskies.jpg
python3 trt_ssd.py --model ssd_mobilenet_v2_egohands --video /data/hands.mp4
python3 trt_ssd.py --model ssd_mobilenet_v1_coco --usb 0 \
  --width 1280 --height 720 --copy_frame
python3 trt_ssd.py --model ssd_mobilenet_v1_coco --rtsp \
  rtsp://user:password@camera/live.sdp --copy_frame
```

The entrypoint uses confidence 0.3 and derives the class dictionary from the
model suffix (`coco` or `egohands`). It draws boxes and confidence labels, adds
smoothed FPS, and supports ESC/fullscreen controls. SSD does not expose a
confidence CLI flag in this entrypoint; call the class API with a chosen
`conf_th` only when writing a controlled adapter.

## 4. Async SSD producer/consumer pipeline

Use `trt_ssd_async.py` when overlapping capture/inference with display is more
important than preserving every frame:

```bash
python3 trt_ssd_async.py --model ssd_mobilenet_v1_coco \
  --video /data/clip.mp4 --video-looping
python3 trt_ssd_async.py --model ssd_mobilenet_v1_coco \
  --usb 0 --width 1280 --height 720 --copy_frame
```

The child thread owns the CUDA context it creates with
`cuda.Device(0).make_context()`. It writes a latest-result tuple under a
condition variable; the display thread waits up to 20 seconds and then exits
with an explicit timeout error. Stop the child and join it before releasing
`Camera`. Do not construct the TensorRT detector in the parent and reuse it in
the child without deliberately redesigning CUDA context ownership.

This is a one-slot/latest-value pipeline: frames can be skipped, and shared
references are replaced. It improves throughput in the historical Jetson
benchmark but is not a latency or ordering guarantee.

## 5. YOLO video file output

`trt_yolo_cv.py` reads a video with OpenCV and writes an annotated video:

```bash
python3 trt_yolo_cv.py --video /data/input.mp4 \
  --output /data/output.mp4 --model yolov4-416
```

It derives the writer size from the capture and uses MP4V at a fixed 30 FPS.
Its loop uses confidence 0.3 and has no camera grab thread, RTSP, USB, or
letterbox CLI beyond the model's `--letter_box` option. Check that the output
codec is available and release both writer and capture on every exit path.

## 6. YOLO MJPEG output

`trt_yolo_mjpeg.py` sends annotated YOLO frames to a small HTTP multipart JPEG
server:

```bash
python3 trt_yolo_mjpeg.py --model yolov4-416 --usb 0 \
  --width 1280 --height 720 --copy_frame --mjpeg_port 8080
```

A client can request `http://<bound-host>:8080/mjpg` (or `/`). The default
server binds all interfaces because `MjpegServer` receives an empty IP string;
choose a protected network and firewall policy before exposing it. The queue
holds at most two frames and silently drops new frames when full. The demo
shuts down the server and releases the camera in `finally` after the loop.

## 7. Stop and evidence protocol

Stop early on any of these gates: no input frame, failed camera open, missing
engine, missing plugin, CUDA context failure, TensorRT deserialize failure,
async timeout, or repeated decoder errors. Save the exact command, stderr,
TensorRT/JetPack version, source mode, model, and first failing stage outside
the runtime tree. A successful visualization window or MJPEG connection proves
plumbing only; it does not establish detection accuracy. Use the repository's
separate evaluation skill and a declared dataset for mAP.
