---
name: video-camera-demos
description: "Guide safe video-file, webcam, and optional half-precision demo
  use for pytorch-yolo-v3."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Video and Camera Demos

Use this sub-skill when a user asks about the repository's video-file demo, webcam demo, or optional half-precision video demo. Keep the interaction focused on safe preflight, command construction, and troubleshooting for these demo entrypoints.

## Route first

- Image or batch-image detection: route to `../image-detection/SKILL.md`.
- Configuration files, model architecture, class names, weight formats, or weight-loading internals: route to `../model-and-config/SKILL.md`.
- Training, dataset preparation for training, and model fine-tuning are out of scope for this sub-skill.

## Safe operating policy

- Do not start a GUI loop, webcam capture, video capture, model inference, download, or weight fetch as a default check.
- Before any full demo run, confirm the user has an intended display path, an accessible video file or camera, required local config/weight files, OpenCV, PyTorch, and permission to use the device.
- Treat CUDA and half precision as optional. Do not claim a full fp16 run is verified unless it was actually run on a CUDA/fp16-capable GPU with the user's files and display.
- Prefer the bundled safe helper for parser/source checks:

  ```bash
  python scripts/check_video_demo_args.py --repo-root <repo-root>
  ```

  Run it from this sub-skill directory or adjust the script path to wherever this skill tree is installed. The helper only invokes `-h` and source inspection; it must not open a webcam, video, display, or model.

- Use the bundled dry-run/launcher wrapper to prepare full demo commands without opening capture/display by default:

  ```bash
  python scripts/run_video_demo.py --repo-root <repo-root> --mode video --video <video-file> --weights <weights-file>
  ```

  Add `--execute --allow-display` only after the user explicitly approves an interactive OpenCV run; camera mode also requires `--allow-camera`.

## What to consult inside this skill

- `references/video-camera-workflows.md` for supported flags, run gates, and demo-specific workflow notes.
- `references/troubleshooting.md` for known failure modes and source-reviewed pitfalls.
- `scripts/check_video_demo_args.py` for deterministic, safe verification that the expected demo scripts and argparse help are present in a user's checkout.
