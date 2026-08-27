---
name: live-demo
description: "Run and troubleshoot MonoGS RealSense live demos and the Open3D/OpenGL GUI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Live Demo

Use this sub-skill when the user asks about live MonoGS capture, Intel
RealSense cameras, USB/device access, GUI behavior, Open3D/GLFW/OpenGL display
errors, or interactive visualization controls.

## Route away

- Base CUDA/PyTorch/submodule installation belongs to `environment-setup`.
- Offline TUM/Replica/EuRoC data and configs belong to `data-and-configs`.
- Offline SLAM commands belong to `offline-slam`.
- Saved-result metrics belong to `evaluation-and-results`.

## Fast path

1. Verify the base MonoGS environment and CUDA extensions first.
2. Install the optional RealSense dependency only when the user will run live
   camera workflows:
   ```bash
   pip install pyrealsense2
   ```
3. Check GUI and camera prerequisites without opening a window:
   ```bash
   python scripts/check_live_demo_prereqs.py --require-cuda
   ```
   Add `--probe-camera` only with an attached RealSense device and user approval.
4. Choose a live config:
   - monocular RealSense: `python slam.py --config configs/live/realsense.yaml`
   - RGB-D RealSense: `python slam.py --config configs/live/realsense_rgbd.yaml`
5. Use USB-3, avoid aggressive motion during initialization, and expect GUI to
   be forced on for `Dataset.type: realsense`.

## Bundled references

- [Live RealSense](references/live-realsense.md) covers camera modes, config
  differences, and safe operation.
- [GUI reference](references/gui-reference.md) describes the visualization
  process, controls, and rendering surfaces.
- [Troubleshooting](references/troubleshooting.md) maps RealSense, Open3D,
  GLFW, OpenGL, and CUDA symptoms to recovery steps.
- [scripts/check_live_demo_prereqs.py](scripts/check_live_demo_prereqs.py) runs
  read-only imports and optional camera probing.
