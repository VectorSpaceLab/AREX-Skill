# Cross-cutting troubleshooting

Read this reference when a route reports an install, import, backend, or artifact problem before using a focused route's troubleshooting file.

## Installation and import

- **`ModuleNotFoundError: nerfstudio`**: install the public distribution (`python -m pip install nerfstudio`) or editable checkout install. Then run `python -c "import nerfstudio; print(nerfstudio.__file__)"` and make sure the command and Python use the same environment.
- **Torch import warns about NumPy ABI**: use a NumPy version compatible with the selected torch wheel; an older Nerfstudio release is safer with `numpy<2` when a compiled dependency was built against NumPy 1.x.
- **`pip check` reports conflicting OpenCV packages**: keep the pinned headless OpenCV variant from the package metadata and avoid mixing a newer `opencv-python` with an older NumPy ABI.
- **Exporter import prints `libOpenGL.so.0` or pymeshlab plugin warnings**: this is a headless-system graphics-library issue. Point-cloud or non-pymeshlab checks may still work; install the host's OpenGL runtime only when mesh operations actually require it.

## CUDA and optional extensions

- **`torch.cuda.is_available()` is false**: check the visible GPU and driver, then install a torch wheel whose CUDA tag is supported by the driver. A CPU import is not evidence that production training/rendering works.
- **`tinycudann` is missing**: select the torch implementation for compatible models or install tiny-cuda-nn with a matching CUDA toolkit/compiler. The torch path is slower and should be treated as a smoke/fallback path.
- **`gsplat` or `nerfacc` import fails**: verify that the package version matches the torch ABI and selected Python/CUDA wheel. Do not silently switch Splatfacto or Instant-NGP to a different implementation.
- **Out-of-memory during training/render/export**: lower rays per batch/chunk, image scale, evaluation frequency, or model size before changing the method. For export, reduce point count/resolution and use a crop box.

## External tools and data

- **`ns-process-data images/video` cannot find COLMAP or FFmpeg**: install both external tools and verify `colmap -h` and `ffmpeg -version`. Device-specific converters such as Polycam/Record3D do not follow the exact COLMAP path.
- **COLMAP returns few/no registered images**: improve overlap, lighting, and sharpness; check that input frames are not blurry or duplicated. Use a small fixture or an existing sparse model to isolate conversion from reconstruction.
- **`transforms.json` cannot find images**: validate paths relative to the dataset directory. The validator in the data-preparation route catches missing files without mutating the dataset.

## CLI and run artifacts

- **`ns-train` ignores a dataparser flag**: tyro applies arguments to the preceding subcommand. Put method flags after the method name and dataparser flags after the dataparser name, for example `ns-train nerfacto --vis viewer nerfstudio-data --eval-mode filename`.
- **Viewer/eval/render/export cannot load a run**: pass the saved `config.yml`, not only a checkpoint directory. Confirm the referenced dataset and checkpoint still exist.
- **Viewer URL is unreachable remotely**: bind/forward the websocket port used by the run (default commonly 7007) and ensure the remote port is allowed. Use the viewer preflight helper before starting the long-running service.
- **Evaluation JSON is missing expected metrics**: confirm the command reached a completed checkpoint and that the output path ends in `.json`. Metric computation can require a valid eval split and enough GPU memory.
