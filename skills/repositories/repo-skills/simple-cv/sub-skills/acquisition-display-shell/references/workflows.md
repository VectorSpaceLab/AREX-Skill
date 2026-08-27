# Acquisition, Display, and Shell Workflows

## When to read this

Read this for SimpleCV frame sources, display handling, shell startup, streams, and calibration. These workflows are often interactive or hardware-sensitive, so prefer finite probes and explicit user confirmation.

## Frame source map

| Class | Use | Caution |
|---|---|---|
| `Camera(camera_index=-1, prop_set={}, threaded=True, calibrationfile='')` | Physical webcam or camera capture | Requires device access and may block or fail on headless hosts. |
| `VirtualCamera(s, st, start=1)` | Image/video-backed frame source | Good substitute for finite checks when a file/video is available. |
| `JpegStreamCamera(url)` | JPEG stream URL | Network/service-dependent. |
| `Kinect(device_number=0)` | Kinect RGB/depth source | Requires `freenect` and hardware. |
| `StereoImage(imgLeft, imgRight)` | Stereo methods from already-loaded images | Safe if inputs are static images. |
| `StereoCamera()` | Live stereo camera workflow | Hardware-dependent. |

## Display map

| Pattern | Use |
|---|---|
| `Display((640, 480))` | Real window/event-loop workflows. |
| `Display(displaytype='notebook')` | Notebook-style output from docs/README. |
| `Display(..., headless=True)` | Dummy SDL finite checks. |
| `Image.save(display)` | Render an image to a display object. |
| `Image.show()` | Development convenience; avoid in non-interactive verification. |

## Finite headless display check

Use the bundled root helper rather than a source example loop:

```bash
SDL_VIDEODRIVER=dummy python ../../scripts/check_display_headless.py
```

Expected signal is `status=ok` with the SimpleCV version and dummy SDL mode.

## Shell startup

The console script is defined by package metadata as `simplecv = SimpleCV.Shell:main`. It opens the interactive shell and prints commands such as `exit()`, `clear()`, `tutorial()`, `example()`, `forums()`, and `walkthrough()`.

Use:

```bash
SDL_VIDEODRIVER=dummy timeout 10 simplecv --help
```

Do not run unbounded shell commands in automation.

## Camera hello-world pattern

Original examples use:

```python
from SimpleCV import Camera
cam = Camera()
img = cam.getImage()
img.show()
```

For user-facing guidance, add these guards:

1. Confirm a camera exists and the process has permission to open it.
2. Set a finite frame count.
3. Save frames or write them to a controlled display instead of infinite `while True` loops.
4. Handle `None`/empty images before downstream detection.

## Virtual camera pattern

Use a virtual source when a camera is not required:

```python
from SimpleCV import VirtualCamera
cam = VirtualCamera('frame.png', 'image')
img = cam.getImage()
```

If using a package sample, first save that sample image to a temporary file from `Image('simplecv')`, then pass that file path to `VirtualCamera`. This keeps the virtual source explicit.

## Calibration pattern

`FrameSource.calibrate(imageList, grid_sz=0.03, dimensions=(8, 5))` consumes a list of images containing chessboards. The interactive tool guides the user through capturing diverse views.

For planning a calibration session:

- Use the interior-corner dimensions, not the square count.
- Use at least several good views; the source warns when too few are provided.
- Save and load calibration matrices with the camera methods when a physical camera is involved.
- Do not run the interactive calibration helper without user approval and hardware readiness.

## Source example replacement map

| Source repo artifact | Runtime replacement |
|---|---|
| `examples/display/simplecam.py` | Finite camera guidance in this reference; do not run infinite loop by default. |
| `examples/display/RenderExample.py` and GUI toolkit examples | Display concepts only; use `check_display_headless.py` for automation. |
| `tools/Calibrate.py` | Calibration checklist here; interactive hardware workflow, not an automatic script. |
| `examples/kinect/*`, `examples/arduino/*`, `examples/web-based/*` | Optional hardware/service notes; no automated runtime dependency. |
| `scripts/simplecv` | Use package console entry point `simplecv` rather than bundling the wrapper. |

## Validation checklist

- Is the task static? If yes, route to image-processing or feature-detection before opening a camera.
- Does the user have hardware and permission? If not, use `VirtualCamera` or sample images.
- Is there a display? If not, set dummy SDL and save outputs.
- Is the loop finite? If not, rewrite it for bounded automation.
- Are optional devices required? If yes, record the required driver/library before proceeding.
