---
name: environment-setup
description: "Install MonoGS, build its CUDA extensions, and verify backend readiness."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---
# environment-setup

Use this sub-skill to prepare a MonoGS runtime before any dataset, SLAM, evaluation, or live-demo work.

## Covers
- Conda environment setup from the checked-in manifest
- Python 3.7 with the reference PyTorch 1.12.1 + CUDA 11.6 stack
- Git submodule initialization for the native extensions
- `simple_knn` and `diff_gaussian_rasterization` build and import checks
- Open3D / OpenGL / GLFW GUI dependencies
- optional `pyrealsense2`

## Does not cover
- dataset layouts and downloads
- offline SLAM command selection or tuning
- RealSense capture operation
- metrics and result interpretation

## Read first
- [Install and backends](references/install-and-backends.md)
- [Troubleshooting](references/troubleshooting.md)

## Verify
Run the bundled checker after install:

- [Environment checker](../../scripts/check_monogs_environment.py)

If that checker is not yet bundled in your checkout, use the smoke commands in the install reference as a temporary fallback.
