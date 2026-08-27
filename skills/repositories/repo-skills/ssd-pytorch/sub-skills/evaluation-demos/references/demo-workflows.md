# Demo workflows and prerequisites

This reference summarizes the repository's notebook and webcam demo behavior so
a Researcher can plan demonstrations without depending on the original notebook
as runtime documentation. The bundled checker verifies imports only; it never
opens a camera, starts Jupyter, or creates GUI windows.

## Notebook-style image demo

The demo notebook workflow is:

1. Import PyTorch, NumPy, OpenCV, plotting tools, repository model/data modules,
   and optionally set CUDA as the default tensor type if CUDA is available.
2. Build an SSD300 test-phase network with 21 VOC classes:
   `build_ssd('test', 300, 21)`.
3. Load a compatible pretrained SSD300 VOC weight file.
4. Load an example image, either from VOC data or from a local sample image.
5. Preprocess the image for SSD300:
   - resize to `300 x 300`,
   - cast to `float32`,
   - subtract the VOC mean values `(104, 117, 123)`,
   - arrange channels/tensor shape as `[1, 3, 300, 300]`.
6. Run a forward pass.
7. Parse detections, scale normalized boxes back to the original image size,
   filter scores at about `0.6`, and draw boxes with class labels.

### Notebook prerequisites

- PyTorch importable in the chosen environment.
- OpenCV Python bindings (`cv2`) for image loading and resizing.
- NumPy.
- Jupyter components plus IPython kernel support.
- Matplotlib for inline display.
- Compatible pretrained SSD300 VOC weights.
- VOC data only if the notebook path uses `VOCDetection`; a standalone sample
  image can avoid dataset access for a simple visualization demo.
- Model-forward compatibility with the installed PyTorch version. If the forward
  pass fails in the Detect layer, route to model-inference.

### Notebook planning notes

- The original notebook is workflow evidence, not a runtime dependency for this
  skill. Recreate the workflow from the steps above when necessary.
- Keep display thresholds high enough for readability. `0.6` is the repository's
  visual default.
- Use CPU unless CUDA is explicitly available and the model/input tensors are
  moved consistently.
- For notebook demos, success means a plausible plotted detection on an image;
  it does not prove VOC mAP reproduction.

## Live webcam demo

The live demo entry point is `python -m demo.live`. Its observed behavior:

- Imports `torch`, `cv2`, `argparse`, and `imutils.video` at module import time.
  Missing `imutils` fails before useful demo setup can run.
- Parses `--weights` with a default VOC0712 SSD300 weight name.
- Parses `--cuda` with legacy `argparse type=bool`; command-line strings such as
  `False` may still parse truthy.
- Builds `build_ssd('test', 300, 21)`, loads the weight file, creates a
  `BaseTransform`, and opens `WebcamVideoStream(src=0)`.
- Uses OpenCV `imshow` and `waitKey` in a loop.
- Draws boxes with a hardcoded confidence threshold of `0.6`.
- Uses `p` to pause/resume and `Esc` to exit.

### Webcam prerequisites

- PyTorch importable; CUDA optional.
- OpenCV Python bindings built with GUI support for the current display system.
- A reachable camera device at the selected OpenCV/imutils source index.
- `imutils` installed.
- Compatible pretrained SSD300 VOC weights.
- A display session that permits `cv2.imshow` windows.
- Model-forward compatibility with the installed PyTorch version.

### Safe live-demo planning

Before attempting the actual webcam command:

```bash
python scripts/check_demo_requirements.py --cuda auto
```

Then verify items the checker intentionally does not test:

- The weight file exists and matches SSD300 VOC.
- The host has an accessible webcam.
- The runtime session has a GUI/display.
- The user is comfortable opening a camera and display window.

Example command template:

```bash
python -m demo.live --weights weights/ssd_300_VOC0712.pth --cuda False
```

For unmodified `demo.live`, treat `--cuda False` as a human-readable template,
not proof that the legacy parser will choose CPU. If CPU/GPU selection matters,
patch or wrap the parser under the model-inference route before relying on it.

## CPU/CUDA behavior

- CPU is acceptable for notebook and webcam demos, but may be slow.
- CUDA can improve speed, but only if all tensors and the network are on CUDA.
- The repository's legacy scripts sometimes set global default tensor types.
  Mixed CPU/CUDA defaults can cause confusing failures in transforms, priors,
  or detection outputs.
- Do not use CUDA as a benchmark claim unless hardware, drivers, installed
  PyTorch build, and model-forward compatibility have all been verified.

## Thresholds and visual readability

- Notebook and live demo parsing use about `0.6` as a confidence threshold.
- Raising the threshold reduces false positives and clutter in demos.
- Lowering the threshold can help diagnose whether the model is producing low
  confidence detections at all.
- These thresholds are for visualization; mAP evaluation should use a low
  threshold and VOC AP computation instead.

## What the bundled checker can and cannot prove

`scripts/check_demo_requirements.py` can prove import availability for the major
Python modules and report CUDA availability from PyTorch. It cannot prove:

- pretrained weight compatibility,
- VOC dataset availability,
- Detect-layer compatibility in a forward pass,
- camera access,
- OpenCV GUI/display support,
- Jupyter server startup or browser access.

Treat checker success as a prerequisite signal, not a complete demo pass.
