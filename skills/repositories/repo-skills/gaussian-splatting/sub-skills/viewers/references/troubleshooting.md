# Viewer Troubleshooting

## Remote Viewer Cannot Connect

Check:

- The optimizer is running without `--disable_viewer`.
- Viewer and optimizer use the same `--ip` and `--port`.
- The port is reachable across containers, VMs, or machines.
- Firewalls are not blocking the connection.

If interactive viewing is not needed, add `--disable_viewer` to training and skip the remote viewer.

## Viewer Cannot Find Source Dataset

When optimizer/model paths are not valid from the viewer environment, pass a source path override:

```bash
SIBR_remoteGaussian_app -s <source-scene>
SIBR_gaussianViewer_app -m <model> -s <source-scene>
```

This is common when training runs in a container or remote machine and the viewer runs on a desktop.

## SIBR Build Fails on Linux

Common causes:

- Missing OpenGL/SIBR system dependencies.
- Missing CMake or compiler.
- The `SIBR_viewers` submodule was not initialized.
- Building with an unsupported OS/library combination.

Use the README's OS-specific dependency list. Do not treat Python environment success as a SIBR build check.

## `cl.exe` or Visual Studio Problems on Windows

The README notes that Windows extension/viewer builds can fail when Visual Studio compiler paths are not available. Ensure the Visual Studio C++ build tools are installed and run from a developer prompt or environment with the compiler on PATH.

## Real-Time Viewer Low FPS

Check:

- Disable V-Sync in the application and GPU driver settings.
- Ensure OpenGL/display GPU and CUDA GPU match in multi-GPU systems.
- Close top view if it slows rendering.
- Toggle fast culling if a visual issue appears.
- Use a reasonable `--rendering-size`.

## CUDA/OpenGL Interop Issues

On systems such as WSL-like environments or mismatched display/CUDA GPUs, interop can fail. Try:

```bash
SIBR_gaussianViewer_app -m <model> --no_interop
```

Performance may be lower.

## Top View Looks Wrong

Use top view camera snapping and image display to verify camera alignment. If input images are not displayed, pass the appropriate source path and image-loading option, and confirm the source dataset layout.
