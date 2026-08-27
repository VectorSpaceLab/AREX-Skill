# Video and Camera Demo Workflows

This reference summarizes the runtime-facing facts for the pytorch-yolo-v3 video and camera demo entrypoints. It is written so an agent can answer user questions and perform safe preflight checks without consulting repository prose or executing a GUI/camera loop.

## Safety boundary

The demo entrypoints are interactive OpenCV programs. Full runs are not safe default validation because they can open windows, touch camera device 0, loop over video frames, require large local weights, and execute model inference. Use bundled helpers first:

```bash
python scripts/check_video_demo_args.py --repo-root <repo-root>
python scripts/run_video_demo.py --repo-root <repo-root> --mode video --video <video-file> --weights <weights-file>
```

`check_video_demo_args.py` runs parser/source checks only. `run_video_demo.py` is a dry-run launcher by default: it validates known prerequisites and prints the command. It executes only with `--execute`, and full execution should be user-approved.

Only proceed to a full run after the user confirms all of the following:

1. They want an interactive demo rather than a parser/precondition check.
2. A display is available for `cv2.imshow`/`cv2.waitKey`, or they have chosen an environment that can show OpenCV windows.
3. The requested input exists: a readable video file for video demos, or an accessible webcam recognized as OpenCV device `0` for the camera demo.
4. Required local model assets are present, especially `yolov3.weights`; no automatic download should be performed by this skill.
5. The selected resolution is a multiple of 32 and greater than 32.
6. Any requested CUDA/fp16 use is backed by an installed CUDA-enabled PyTorch and a GPU that supports useful fp16 execution.

## Demo entrypoint matrix

| Entrypoint | Purpose | User-facing flags | Defaults and notes |
| --- | --- | --- | --- |
| `video_demo.py` | Run YOLOv3 detection on a video file. | `--video`, `--dataset`, `--confidence`, `--nms_thresh`, `--cfg`, `--weights`, `--reso` | `--video` defaults to `video.avi`; `--dataset` defaults to `pascal`; confidence defaults to `0.5`; NMS threshold defaults to `0.4`; config defaults to `cfg/yolov3.cfg`; weights default to `yolov3.weights`; resolution defaults to `416`. |
| `cam_demo.py` | Run YOLOv3 detection from webcam device `0`. | `--confidence`, `--nms_thresh`, `--reso` | Uses hard-coded `cfg/yolov3.cfg` and `yolov3.weights`; captures `cv2.VideoCapture(0)`; confidence defaults to `0.25`; NMS threshold defaults to `0.4`; resolution defaults to `160`. |
| `video_demo_half.py` | Experimental video demo path that uses half precision when CUDA is available. | `--video`, `--dataset`, `--confidence`, `--nms_thresh`, `--cfg`, `--weights`, `--reso` | Parses the same visible flags as `video_demo.py`, but source review shows the runtime video path is hard-coded to `video.avi`. Its help description says `YOLO v2 Video Detection Module` even though the file is the YOLOv3 half demo. |

## Safe parser and source check

From this sub-skill directory, use:

```bash
python scripts/check_video_demo_args.py --repo-root <repo-root>
```

The helper verifies that the three demo scripts are present, runs each script with `-h`, extracts argparse flags from source, and reports known pitfalls. It does not open a GUI, camera, video, model, or weights file.

Use this helper when the user is on a headless server, lacks a camera, only wants to understand flags, or asks why a demo option appears to be ignored.

## Video-file demo workflow

Use video mode in the bundled wrapper for normal video-file inference preflight:

```bash
python scripts/run_video_demo.py \
  --repo-root <repo-root> \
  --mode video \
  --video <video-file> \
  --cfg cfg/yolov3.cfg \
  --weights <weights-file> \
  --reso 416 \
  --confidence 0.5 \
  --nms-thresh 0.4
```

To execute after approval, add `--execute --allow-display`.

Important constraints:

- The underlying demo asserts that `cv2.VideoCapture(<video>)` opens successfully; otherwise it raises `Cannot capture source`.
- OpenCV codec support is build-dependent. The repository-facing expectation is an AVI-style input such as `video.avi`, but the true gate is whether the installed OpenCV can open the file.
- The loop displays every processed frame with `cv2.imshow("frame", ...)` and waits with `cv2.waitKey(1)`; this requires a display and is unsuitable for default headless execution.
- The demo loads classes and palette data during frame processing, so the working checkout must include the expected local data files as well as config and weights.

Do not run a full video command as a validation substitute for the safe helper.

## Webcam demo workflow

Use camera mode only when the user explicitly wants live webcam inference and has a GUI-capable environment:

```bash
python scripts/run_video_demo.py \
  --repo-root <repo-root> \
  --mode camera \
  --reso 160 \
  --confidence 0.25 \
  --nms-thresh 0.4
```

To execute after approval, add `--execute --allow-display --allow-camera`.

Key facts:

- The camera demo always opens OpenCV device `0`; there is no CLI flag for another camera index.
- It hard-codes `cfg/yolov3.cfg` and `yolov3.weights`.
- Its default resolution is `160`, not `416`.
- It displays frames through `cv2.imshow` and exits the loop when `q` is pressed in the OpenCV window.
- Source review found a CUDA-only bug: the CUDA branch references `im_dim` before assigning it. A CPU-only run avoids that specific line, but still needs camera, display, weights, and dependencies.

If the user has no camera or is on a headless server, use the safe helper instead of attempting a run.

## Half-precision video workflow

Treat half mode as an optional experimental path, not as a general replacement for normal video mode:

```bash
python scripts/run_video_demo.py \
  --repo-root <repo-root> \
  --mode half \
  --video video.avi \
  --cfg cfg/yolov3.cfg \
  --weights <weights-file> \
  --reso 416
```

To execute after approval, add `--execute --allow-display`. If the user asks for a custom video filename in half mode, the wrapper warns that the underlying source ignores custom `--video` at runtime; execution with that pitfall requires explicit `--accept-half-hardcode` after the user chooses a workaround.

Source-reviewed caveats:

- Half precision only makes sense with CUDA enabled and a GPU with useful fp16 support.
- Do not claim speedups or correctness unless a full user-approved run is actually performed in the target environment.
- Although the half demo parses `--video`, source review shows the runtime variable is hard-coded to `video.avi`; a command such as `--video custom.avi` will still try to use `video.avi` unless the user's checkout is changed or the input is made available under that name.
- The help description says `YOLO v2 Video Detection Module`; treat this as a stale description string, not evidence that the file is for a different model family.

For a custom video filename, prefer normal video mode. If the user specifically wants the half demo with a custom filename, explain the hard-coded path and ask before suggesting a local source edit or a safe filesystem-level workaround such as providing the intended input under the expected filename.
