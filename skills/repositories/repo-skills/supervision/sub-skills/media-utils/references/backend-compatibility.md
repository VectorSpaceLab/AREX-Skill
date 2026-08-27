# Backend compatibility

Supervision `0.31.0.dev0` no longer requires OpenCV as an installed package.
Image, drawing, and file-video APIs use an internal compatibility layer that
selects either an already-installed `cv2` module or a bundled pure NumPy/Pillow/
PyAV fallback at import time.

## Default fallback behavior

A normal install is enough for package-owned APIs:

```bash
pip install supervision
```

When `cv2` is absent, importing `supervision` can emit a warning that the pure
NumPy fallback backend is active. This is expected. The fallback keeps documented
Supervision image, drawing, and file-video helpers operational, but pixel-exact
text rendering, anti-aliased lines, codecs, and performance can differ from
native OpenCV.

Diagnostic check:

```bash
python -c "from supervision import _cv2; print(_cv2.BACKEND_NAME)"
```

Use `_cv2` only as a diagnostic. Application code should call public
`supervision` helpers.

## Choosing native OpenCV

Install exactly one OpenCV wheel family only when the application needs native
OpenCV behavior, webcam capture, GUI support, or broader codec behavior:

```bash
# Servers and containers without GUI modules
pip install opencv-python-headless supervision

# Desktop applications that need OpenCV GUI windows
pip install opencv-python supervision
```

Do not install both `opencv-python` and `opencv-python-headless` in the same
environment. If another model runtime already installed a compatible `cv2`, do
not add a second wheel family.

Backend selection happens once per fresh Python process. After changing OpenCV
packages, restart the Python process before re-checking `_cv2.BACKEND_NAME`.

## Webcam and live capture ownership

Supervision's video helpers operate on local video files and arrays. Live webcam
capture is application-owned:

```python
import cv2
import supervision as sv

capture = cv2.VideoCapture(0)
annotator = sv.BoxAnnotator()

while True:
    ok, frame = capture.read()
    if not ok:
        break
    detections = predict_as_detections(frame)
    annotated = annotator.annotate(scene=frame.copy(), detections=detections)

capture.release()
```

If the user asks for webcam capture, discuss the chosen OpenCV wheel and device
permissions rather than trying to make `sv.get_video_frames_generator` open a
camera index.

## GUI windows

`sv.ImageWindow` and the bundled `tracking-keypoints/scripts/draw_zones.py`
helper are for desktop or display-capable sessions. In headless containers,
prefer saving images/videos, notebook plotting, or web UI code outside
Supervision.

Typical GUI failure causes:

- No `$DISPLAY` or equivalent display server.
- `opencv-python-headless` installed when GUI windows are expected.
- Tk/Pillow windowing support unavailable.
- Running over SSH without X forwarding or a virtual display.

## Video codecs and PyAV

The base package includes PyAV for video file handling. Native OpenCV may still
be useful for environments with specific codec expectations or existing OpenCV
pipelines. For reproducible scripts:

- Use local file paths, not webcams or streams, with `get_video_frames_generator`.
- Record the expected frame resolution and FPS using `VideoInfo.from_video_path`.
- Make `VideoSink` frames match `VideoInfo.width` and `VideoInfo.height`.
- If audio preservation matters, use `process_video(..., preserve_audio=True)`
  only after confirming the source file and codec support.

## When to route elsewhere

- If backend behavior affects mask/box rendering through high-level annotators,
  pair this reference with [annotators](../../annotators/SKILL.md).
- If backend behavior affects model-result masks, tiled inference, or zones,
  pair it with [detection-and-zones](../../detection-and-zones/SKILL.md).
- If the task is only dataset conversion or metric computation, backend details
  usually matter only for optional visualization.
