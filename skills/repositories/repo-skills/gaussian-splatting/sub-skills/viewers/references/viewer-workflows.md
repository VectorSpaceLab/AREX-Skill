# Viewer Workflows

## When To Read

Read this for the SIBR remote/network viewer, real-time viewer, build commands, navigation, top view, and OpenXR notes.

## Build or Install Viewer Binaries

The README provides two routes:

- Download prebuilt Windows binaries when using Windows.
- Build from `SIBR_viewers` when the submodule source is available.

Linux 22.04 build shape:

```bash
sudo apt install -y libglew-dev libassimp-dev libboost-all-dev libgtk-3-dev libopencv-dev libglfw3-dev libavdevice-dev libavcodec-dev libeigen3-dev libxxf86vm-dev libembree-dev
cd SIBR_viewers
cmake -Bbuild . -DCMAKE_BUILD_TYPE=Release
cmake --build build -j24 --target install
```

Windows build shape:

```bash
cd SIBR_viewers
cmake -Bbuild .
cmake --build build --target install --config RelWithDebInfo
```

Do not start a SIBR build as a hidden verification step; it downloads/builds external dependencies and can take significant time.

## Network Viewer Flow

The network viewer connects to a running optimizer. Defaults are `127.0.0.1` and port `6009`.

Viewer side:

```bash
<install-bin>/SIBR_remoteGaussian_app
```

Optimizer side:

```bash
python train.py -s <scene> --ip 127.0.0.1 --port 6009
```

If optimizer and viewer run on different machines or containers, make sure the IP/port are reachable and pass a source-path override to the viewer if the optimizer's data path is not valid from the viewer machine.

## Real-Time Viewer Flow

After training:

```bash
<install-bin>/SIBR_gaussianViewer_app -m <trained-model>
```

Useful options:

- `-m` / `--model-path`: trained model directory.
- `--iteration`: specific saved iteration.
- `-s` / `--path`: source dataset path override.
- `--rendering-size <width> <height>`: rendering resolution.
- `--force-aspect-ratio`: enforce a non-input aspect ratio.
- `--load_images`: load source images for top view/camera display.
- `--device`: CUDA device index.
- `--no_interop`: disable CUDA/OpenGL interop when needed.

## Navigation and Top View

Default navigation is FPS-style: `W/A/S/D/Q/E` for translation and `I/K/J/L/U/O` for rotation. Trackball-style navigation is available from the floating menu.

The top view shows the SfM point cloud, input cameras, and the user camera. It can display input images, snap to input cameras, and help diagnose camera alignment. It can slow rendering when enabled.

## Antialiasing and Viewer Display

If a scene was trained with `--antialiasing`, enable the corresponding viewer antialiasing option when inspecting it interactively.

## OpenXR Note

OpenXR support is documented for a separate branch. Do not promise OpenXR behavior from the default branch unless the user is explicitly using the OpenXR branch and the matching SIBR documentation.
