# GUI Reference

## Process model

When `Results.use_gui` is true, MonoGS starts a separate GUI process. The main
SLAM process sends `GaussianPacket` objects through queues; the GUI process
renders camera frustums, keyframes, current input images, depth/opacity views,
and the Gaussian cloud.

Live RealSense mode always enables the GUI. Offline configs can disable it by
setting `Results.use_gui: false`, or by using `--eval`, which forces headless
mode.

## Rendering stack

The GUI uses:

- Open3D application and scene widgets for the main window.
- GLFW to create a hidden OpenGL context named `headless rendering`.
- PyOpenGL for low-level OpenGL calls.
- bundled GLSL shaders for Gaussian rendering.
- CUDA/PyTorch sorting of Gaussians before OpenGL buffer updates.

A Python import check is not enough to prove the GUI will open: the host also
needs a usable display server or an approved virtual display path.

## Main controls exposed in the GUI

- Resume/Pause toggle sends pause/unpause messages to the SLAM process.
- Camera follow and "From Behind" options select the view behavior.
- Viewpoint list jumps to stored keyframes.
- Cameras, active window, and axis toggles control scene overlays.
- Depth, opacity, time shader, and ellipsoid shader toggles switch rendering
  modes.
- Gaussian scale slider changes the render scale modifier.
- Screenshot button writes screenshots from the GUI process.

## When to disable GUI

Disable GUI for batch/evaluation runs, SSH sessions without display forwarding,
or maximum GPU throughput. Because `slam.py` has no `--headless` flag, make a
config copy with `Results.use_gui: false` or use `--eval` for evaluation runs.
Do not use live RealSense configs for headless operation because live mode forces
GUI on.
