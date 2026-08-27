---
name: acquisition-display-shell
description: "Guides SimpleCV camera acquisition, virtual cameras, display
  windows, shell startup, streams, calibration, and headless runtime checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Acquisition, Display, and Shell

Use this sub-skill when the difficult part is acquiring frames, displaying frames, starting the shell, handling interactive loops, or explaining optional hardware.

## Read first

Read `references/workflows.md` for camera, display, shell, stream, and calibration patterns.
Read `references/troubleshooting.md` for headless SDL, webcam, device, and shell-start failures.
Run `scripts/env_probe.py --help` for safe environment probes that do not open a physical camera.
Use the root `../../scripts/check_display_headless.py` for a finite dummy-SDL `Display` smoke.

## Use this for

- `Camera`, `VirtualCamera`, `JpegStreamCamera`, `StereoImage`, and `StereoCamera` routing.
- `Display`, `Image.show()`, display loops, `Display(..., headless=True)`, and notebook display mode.
- The `simplecv` interactive shell and shell help/banner behavior.
- `Stream`, JPEG streamers, web display concepts, and finite display probes.
- Calibration workflow planning from images or a physical camera.
- Optional devices such as Kinect, Vimba/AVT cameras, scanners, digital cameras, and screenshot capture.

## Route elsewhere

- Static transforms or sample-image processing → `../image-processing-basics/SKILL.md`.
- Detector algorithms on a frame/image → `../feature-detection/SKILL.md`.
- Stateful masks and trackers → `../segmentation-tracking/SKILL.md`.
- Classifier training/testing → `../machine-learning-legacy/SKILL.md`.

## Safe acquisition workflow

1. Check package import and OpenCV compatibility with `../../scripts/check_env.py`.
2. In headless environments, set `SDL_VIDEODRIVER=dummy` before importing pygame-backed display code.
3. For static or automated tests, prefer `VirtualCamera` or sample images over `Camera(0)`.
4. Only instantiate `Camera`, Kinect, Vimba, scanner, or digital camera objects when the user explicitly confirms hardware availability.
5. Keep loops finite in scripts; original examples often run `while True` or wait for mouse input.

## Shell workflow

The `simplecv` console entry point starts an interactive shell. To smoke-check it in automation, use a timeout:

```bash
SDL_VIDEODRIVER=dummy timeout 10 simplecv --help
```

A printed banner plus prompt is a successful shell-start signal, not necessarily a command that should exit by itself.

## Calibration workflow

Use calibration guidance when the user has a camera and a printed chessboard. The source calibration tool is interactive and should be treated as a workflow reference, not copied as an automatic script. For automated checks, use stored calibration fixtures only after the full skill is integrated.

## Bundled helper

```bash
python sub-skills/acquisition-display-shell/scripts/env_probe.py
SDL_VIDEODRIVER=dummy python ../../scripts/check_display_headless.py
```

Use `--repo-root` only for an explicit target checkout.

## Verification hooks

Good final candidates include the bounded `simplecv --help` shell smoke, headless `Display` construction, virtual-camera-only native tests, and stereo/calibration fixture tests when they are safe. Physical camera, Kinect, Vimba, scanner, and web/Flash examples are optional hardware/service workflows and should not block core CPU verification.
