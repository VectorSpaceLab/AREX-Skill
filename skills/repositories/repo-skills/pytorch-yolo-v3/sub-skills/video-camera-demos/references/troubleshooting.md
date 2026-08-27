# Video and Camera Troubleshooting

Use this reference to answer operational questions about the video, camera, and optional half-precision demos. Prefer safe parser/source checks before full runs, especially on headless systems or machines without a camera.

## Quick safe triage

Run the bundled helper instead of a full demo when the user only needs flags, preconditions, or source-reviewed pitfalls:

```bash
python scripts/check_video_demo_args.py --repo-root <repo-root>
```

This check invokes each demo with `-h` and inspects source text. It must not open a GUI, camera, video stream, model, weights file, or network connection.

For a full-run preflight that still defaults to no execution, use the bundled launcher wrapper:

```bash
python scripts/run_video_demo.py --repo-root <repo-root> --mode video --video <video-file> --weights <weights-file>
```

Only add `--execute --allow-display` after approval; camera mode also requires `--allow-camera`.

## Common symptoms and fixes

| Symptom | Likely cause | Safe diagnosis | Recommended response |
| --- | --- | --- | --- |
| `Cannot capture source` | `cv2.VideoCapture(...)` failed. For video demos, the file path may be missing, unsupported, or unreadable. For the camera demo, OpenCV device `0` may be absent, busy, or permission-denied. | Use the helper to confirm the entrypoint and flags without capture. Separately ask the user to confirm the file path or camera availability before any full run. | For video, use an existing readable input that the installed OpenCV can open, with AVI safest for this repository's intended workflow. For webcam, only run on a machine with camera device `0` and user permission. |
| No display, `cv2.imshow` error, Qt/X11/GTK error, or hang on a server | All three demos call `cv2.imshow("frame", ...)` and `cv2.waitKey(1)` inside the processing loop. | Do not run a full demo as a test on a headless server. Use the helper for parser/source checks. | Tell the user a GUI-capable session is required for these demo scripts. If they need non-GUI batch image inference, route to [../../image-detection/SKILL.md](../../image-detection/SKILL.md); if they need code changes for headless video output, treat that as a separate modification request. |
| Missing `yolov3.weights` or weight-loading failure | Full demos load weights before processing input. `cam_demo.py` hard-codes `yolov3.weights`; the video demos default to it unless `--weights` is supplied. | The helper can confirm CLI support without touching weights, but it cannot validate model loading. | Ask the user to provide a local weights path or place the expected weights file in the checkout. Do not download weights automatically. Route internals of weight formats/loading to [../../model-and-config/SKILL.md](../../model-and-config/SKILL.md). |
| `video_demo_half.py --video custom.avi` still uses `video.avi` | Source review shows `video_demo_half.py` parses `--video` but later assigns `videofile = 'video.avi'`. | Use the helper; it reports both the parsed `--video` flag and the hard-coded runtime pitfall. | Explain that the flag is ignored by the half demo's runtime code. Prefer `video_demo.py` for custom video filenames. If the user insists on the half demo, ask before suggesting a local edit to use `args.video` or a safe workaround that makes the intended input available as `video.avi`. |
| Half precision has no effect or is unavailable | `video_demo_half.py` only moves the model/tensors to half precision in the CUDA branch. CPU-only PyTorch will not provide a meaningful fp16 speed path. Some GPUs have poor fp16 throughput. | Ask whether `torch.cuda.is_available()` is true in the user's environment; do not run a full GPU demo unless requested. | Treat fp16 as optional and environment-dependent. Do not claim verified fp16 performance without an actual user-approved CUDA run. |
| `cam_demo.py` crashes only when CUDA is available | Source review found `im_dim = im_dim.cuda()` in the CUDA branch while the prior `im_dim` assignment is commented out. | The helper reports this source pitfall. A parser-only check will not trigger the crash because it does not enter the loop. | Explain the CUDA-only `im_dim` bug. A CPU path avoids that specific line, but a real webcam run still needs camera, display, weights, and dependencies. If the user wants CUDA webcam support, ask before proposing a checkout patch. |
| OpenCV cannot read a non-AVI file or reads zero frames | Codec/container support depends on the installed OpenCV build. The repository workflow expects AVI-style video input, but OpenCV behavior varies. | Confirm the path exists and the user can open it with their local OpenCV tooling before a full run. The helper only checks argparse and source. | Use an input format supported by the user's OpenCV build; AVI is the safest starting point for this repository's demo assumptions. |
| Resolution assertion failure | Demo code asserts the network resolution is a multiple of 32 and greater than 32. | Check the command's `--reso` value. | Use values such as `160` for the webcam default or `416` for the video default; any custom value should satisfy `reso % 32 == 0 and reso > 32`. |
| Confusion from `YOLO v2 Video Detection Module` in half-demo help | The half-demo argparse description string is stale. | The helper reports the help description for each script. | Treat the file as the repository's YOLOv3 half-precision video demo despite the stale help text. |

## Response patterns for hard usability cases

### Custom video ignored by the half demo

When the user asks why `video_demo_half.py --video custom.avi` still opens `video.avi`, answer directly: the file parses `--video` but then hard-codes `videofile = 'video.avi'` before opening `cv2.VideoCapture`. Recommend the normal video demo for arbitrary filenames. Only propose editing the user's checkout or creating a local alias after the user confirms that such a change is acceptable.

### Headless server or no camera

When the user is on a server without a display or camera, do not try to run a full video or camera demo as a validation step. Run only the bundled safe helper for flags and source pitfalls. If the user's real goal is non-interactive detection, route image inference to [../../image-detection/SKILL.md](../../image-detection/SKILL.md) or treat headless video export as a separate implementation task.
