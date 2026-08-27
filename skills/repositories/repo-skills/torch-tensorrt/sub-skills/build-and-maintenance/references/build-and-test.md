# Build and Test Guidance

## Source build essentials

The source tree documents a Bazel-centered build with optional Python-only, no-TorchScript, RTX, JetPack, and Windows ARM64 variants. Before starting a full build, verify:

- Python version and environment manager.
- Matching PyTorch/CUDA/TensorRT family for the intended wheel.
- Bazel/Bazelisk and any platform-specific compiler/toolchain requirements.
- Whether the user wants a standard wheel, TensorRT-RTX wheel, or a special platform build.

## Smallest safe commands

Use read-only or light-weight checks first:

```bash
python scripts/source_build_probe.py --help
python -m pip show torch torch-tensorrt tensorrt tensorrt_rtx
```

If the user wants a source install, prefer the documented install/build variant that matches the target:

- `python -m pip install --pre . ...` for editable/local installs.
- `PYTHON_ONLY=1` when the Python-only runtime is desired.
- `NO_TORCHSCRIPT=1` when the legacy frontend is not needed.
- `USE_TRT_RTX=1` for RTX builds.
- `TORCHTRT_TARGET_PLATFORM=windows-arm64` or `--windows-on-arm` for Windows ARM64 cross-builds.

## Maintain safe test lanes

| Task | Preferred check |
| --- | --- |
| Package import/feature sanity | Root environment probe |
| Source build prerequisites | `scripts/source_build_probe.py` |
| CI lane discovery | `scripts/list_ci_suites.py` |
| Repository maintainer diagnosis | `tests/README.md`, `tests/NOTES.md`, `tests/ci/suites.py` |

## What a maintainer answer should include

- Target platform and variant.
- Whether TorchScript/C++ runtime is needed.
- Which test lane or build command is being selected and why.
- What prerequisites are missing if the build is not yet runnable.
- A warning when a requested combination is unsupported or optional-only.
