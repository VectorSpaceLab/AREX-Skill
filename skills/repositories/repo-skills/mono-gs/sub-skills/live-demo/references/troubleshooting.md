# Live Demo Troubleshooting

## `pyrealsense2` import fails

Symptoms:
- `ModuleNotFoundError: No module named 'pyrealsense2'`.
- The live config fails before opening the pipeline.

Recover:
1. Install `pyrealsense2` in the active MonoGS environment only when live camera
   support is required.
2. Re-run `scripts/check_live_demo_prereqs.py --require-realsense`.
3. If wheels are unavailable for the Python/platform, switch to a supported
   Python/OS or use offline datasets instead.

## No RealSense device or stream failure

Symptoms:
- Pipeline start fails.
- No RGB/depth frames arrive.
- RGB-D alignment errors appear.

Recover:
1. Confirm the camera is connected to USB-3 and visible to RealSense tools.
2. Check OS device permissions and that no other process owns the camera.
3. Use `scripts/check_live_demo_prereqs.py --probe-camera` only with user
   approval; it attempts a read-only SDK device query.
4. Fall back to offline TUM/Replica/EuRoC workflows when camera hardware is not
   available.

## Open3D/GLFW/OpenGL window errors

Symptoms:
- GLFW initialization fails.
- Open3D cannot create a window.
- `ImportError` or GL context errors appear around `OpenGL`, `glfw`, or Open3D
  visualization modules.

Recover:
1. Verify `open3d`, `glfw`, `OpenGL.GL`, `imgviz`, and CUDA with the bundled
   prerequisite checker.
2. Use a local desktop session or an approved virtual display/remote OpenGL
   setup. SSH without X11/Wayland forwarding is usually insufficient.
3. For offline non-live work, set `Results.use_gui: false` or use `--eval`.
4. Do not expect live RealSense configs to run headless; `Dataset.type:
   realsense` forces GUI on.

## Tracking is unstable during live initialization

Symptoms:
- Map resets, tracking diverges, or Gaussian cloud appears incoherent.

Likely causes:
- Aggressive camera motion before initialization stabilizes.
- Rolling-shutter or low-light camera behavior.
- Exposure/white-balance changes.

Recover:
1. Move slowly for the first 15 seconds.
2. Prefer a global-shutter RealSense model and stable lighting.
3. Use RGB-D live config when depth is available.
4. Reduce scene complexity or switch to an offline dataset for reproducible
   debugging.
