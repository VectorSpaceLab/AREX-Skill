# Live RealSense Workflows

## Supported live configs

| Config | Sensor mode | What it does |
| --- | --- | --- |
| `configs/live/realsense.yaml` | `monocular` | Streams RGB frames and initializes depth synthetically for monocular SLAM. |
| `configs/live/realsense_rgbd.yaml` | `depth` | Streams RGB and aligned depth frames from the RealSense device. |

MonoGS treats `Dataset.type: realsense` as live mode. In `SLAM.__init__`, live
mode forces `use_gui=True` even if a config tries to disable the GUI.

## Hardware and package requirements

- Intel RealSense camera tested by the project: D455-like global shutter camera.
- USB-3 connection; avoid USB-2 ports for bandwidth and synchronization.
- `pyrealsense2` installed in the active MonoGS environment.
- CUDA-capable PyTorch and MonoGS CUDA extensions; live mode still uses the same
  Gaussian renderer and model backend as offline runs.
- Display/OpenGL stack capable of running Open3D GUI and a hidden GLFW OpenGL
  context.

## Camera behavior in the loader

`RealsenseDataset` starts a `pyrealsense2.pipeline`, enables a 1280x720 BGR8
color stream at 30 FPS, and optionally enables a depth stream when
`Dataset.sensor_type: depth`.

For RGB-D live mode it aligns depth to the color stream, converts depth to
meters with the device scale, and uses the live camera intrinsics from the
RealSense profile. For monocular live mode it uses color only and returns
`depth=None`.

## Operation tips

- Move slowly during the first seconds so initial bundle adjustment can
  stabilize.
- Prefer a global-shutter RealSense model for robust tracking.
- Keep lighting stable; aggressive exposure/white-balance changes can make
  tracking harder.
- Start with monocular live config only when depth is unavailable; RGB-D mode
  gives the SLAM system real depth observations.
- Do not try to use `--eval` for live camera workflows; evaluation assumes an
  offline dataset with ground truth.
