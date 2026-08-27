# Setup and Backend Troubleshooting

## When to read

Read this when the install, editable build, import, or asset staging step fails.
Each row names the symptom, likely cause, and the next repair step.

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ImportError: ... libtorch_cpu.so: undefined symbol: iJIT_NotifyEvent` | MKL/OpenMP versions from the solver are incompatible with the torch wheel | Downgrade to a torch-compatible MKL/OpenMP set such as `mkl<2025` and `intel-openmp<2025`, then re-run `pip check`. |
| `ModuleNotFoundError: torch` while building `curope` or another local dependency | Build isolation hid the already-installed torch package | Re-run the editable install with `--no-build-isolation` after torch is already installed. |
| `cuda_runtime.h: No such file or directory` | nvcc is present, but CUDA headers/dev packages are missing | Install `cuda-cudart-dev` and the matching CUDA development packages into the private prefix. |
| `CUDA not found, cannot compile backend!` | `torch.cuda.is_available()` was false at build time or torch was CPU-only | Install a CUDA-enabled torch build and ensure the host sees a real NVIDIA GPU. |
| `mast3r_slam_backends` imports fail after install | The root editable install never completed or the extension build was interrupted | Re-run the root install after confirming `nvcc`, `cuda_runtime.h`, and `ninja` are available. |
| `opencv-python 5.x` conflicts with repo-pinned `numpy==1.26.4` | The newest OpenCV wheel expects NumPy 2 | Pin `opencv-python==4.10.0.84` instead of upgrading NumPy. |
| `dust3r` cannot be imported in a custom notebook/snippet | The MASt3R path hook was not initialized | Import `mast3r.utils.path_to_dust3r` first, or use the MASt3R-SLAM helpers that do it for you. |
| Checkpoint files are missing | The repo does not auto-download assets | Use `scripts/checkpoint_manifest.py` and the README URLs, then verify filenames locally. |
| RealSense or visualization imports fail | Optional hardware/UI packages are missing | Install `pyrealsense2`, `in3d`, `moderngl`, `glfw`, and `imgui` only when the workflow needs them. |

## Recovery order

1. Confirm the private environment path, Python version, and CUDA availability.
2. Fix the build toolchain before re-running any editable install.
3. Re-run `python -m pip check`.
4. Re-run `scripts/check_install.py --check-cuda`.
5. Only after the backend is healthy should you return to `run-slam` or
   `evaluation`.
