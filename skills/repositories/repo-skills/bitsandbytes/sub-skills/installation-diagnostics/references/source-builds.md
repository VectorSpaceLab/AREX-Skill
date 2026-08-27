# Source Builds

Use source builds when a wheel cannot match the user's accelerator runtime, CPU architecture, platform ABI, or desired backend. Prefer wheel installs first for standard supported environments; source builds add compiler/toolkit complexity and should be scoped to the backend actually needed.

## When to Recommend a Source Build

- The requested native library, such as `libbitsandbytes_cuda130` or `libbitsandbytes_rocm72`, is not bundled in the installed wheel.
- PyTorch reports a CUDA or ROCm version that has no matching prebuilt bitsandbytes binary for the user's platform.
- The user is on Jetson/L4T/JetPack, where generic Linux aarch64 CUDA wheels are not ABI-compatible with Jetson CUDA libraries.
- The GPU compute capability or ROCm gfx target is not included in the wheel's target list.
- The user is working from a source checkout and sees a message implying the library was not compiled.
- The user needs CPU-only, CUDA, ROCm/HIP, XPU, or MPS backend artifacts for local development.

Do not recommend source builds for Hugging Face quantization configuration mistakes, optimizer API misuse, or model memory pressure by default; route those to the relevant sibling sub-skill.

## Build Tool Minimums

| Backend | Minimum tools and notes |
| --- | --- |
| CPU | Python 3.10+, PyTorch 2.4+, C++ compiler. CPU source installs can often be triggered by `pip install .` or `pip install -e .` from a source tree. |
| CUDA | CMake 3.22.1+, Python 3.10+, C++ compiler, CUDA Toolkit 11.8 through 13.0, and a CUDA compiler first on `PATH`. GCC 11+ is recommended on Linux; Visual Studio 2022 with C++ support is needed on Windows. |
| ROCm/HIP | CMake 3.31.6+ is recommended for ROCm builds, Python 3.10+, C++ compiler, ROCm 6.2 or newer, and optional explicit `BNB_ROCM_ARCH`. Windows HIP builds need Visual Studio 2022, Ninja, CMake, Python, and ROCm SDK wheels or an equivalent SDK setup. |
| XPU | Build uses the `xpu` compute backend and oneAPI/SYCL-related stack. Prefer official wheels unless doing development or diagnosing wheel unavailability. |
| MPS | macOS only; use the `mps` compute backend. CUDA/HIP are invalid on macOS. |

## Backend Selection Commands

These commands are templates for a source tree. They are intentionally local and do not download toolkits or modify system drivers.

```bash
# CPU backend
cmake -DCOMPUTE_BACKEND=cpu -S .
cmake --build . --config Release
python -m pip install .

# CUDA backend
cmake -DCOMPUTE_BACKEND=cuda -S .
cmake --build . --config Release
python -m pip install .

# CUDA backend with explicit GPU targets
cmake -DCOMPUTE_BACKEND=cuda -DCOMPUTE_CAPABILITY="75;80;90" -S .
cmake --build . --config Release
python -m pip install .

# ROCm/HIP backend
cmake -DCOMPUTE_BACKEND=hip -S .
cmake --build . --config Release
python -m pip install .

# ROCm/HIP with explicit target architecture and output version name
cmake -DCOMPUTE_BACKEND=hip -DBNB_ROCM_ARCH="gfx90a;gfx942" -DROCM_VERSION=72 -S .
cmake --build . --config Release
python -m pip install .

# XPU backend
cmake -DCOMPUTE_BACKEND=xpu -S .
cmake --build . --config Release
python -m pip install .

# macOS MPS backend
cmake -DCOMPUTE_BACKEND=mps -S .
cmake --build . --config Release
python -m pip install .
```

On single-config generators such as Unix Makefiles, `make` is equivalent to `cmake --build .` after configuration. On Visual Studio generators, keep `--config Release`.

## CUDA Build Decisions

- CUDA version is discovered from the CUDA compiler found by CMake. The `CUDA_VERSION` CMake cache variable is a sanity check; it does not replace the compiler. If it disagrees with the compiler version, configuration fails.
- Put the intended `nvcc` first on `PATH` before configuring. Stale `PATH`, `CUDA_HOME`, or `LD_LIBRARY_PATH` entries can cause a successful build that links against the wrong runtime.
- CUDA Toolkit versions below 11.8 are unsupported; CUDA 14 or newer is outside the supported build range.
- Use `COMPUTE_CAPABILITY` to limit or expand GPU architectures. Examples: `87` for many Orin Jetson devices, `72` for Xavier, `89` for Ada, `90` for Hopper. Confirm the exact device capability before building.
- For `no kernel image available`, compare both the GPU compute capability and the CUDA toolkit target set. Rebuild with a target including the user's GPU if the wheel omitted it.

## ROCm Build Decisions

- ROCm builds use `COMPUTE_BACKEND=hip`.
- The output filename normally follows the ROCm version. `-DROCM_VERSION=72` can force a `libbitsandbytes_rocm72` style name when PyTorch reports a different ROCm version than the system build tools.
- Use `BNB_ROCM_ARCH` to target specific GPUs, such as `gfx90a`, `gfx942`, or `gfx1100`.
- If `BNB_ROCM_VERSION` is needed at runtime, ensure it matches the built library filename, not just the system ROCm install.

## Jetson / aarch64 Guidance

For Jetson devices, generic Linux aarch64 CUDA wheels are not sufficient even when the GPU compute capability appears compatible. The CUDA library and ABI layer differs under L4T/JetPack. Recommend either:

1. Build on the Jetson device with the correct CUDA toolkit and explicit `COMPUTE_CAPABILITY`, then install the local build.
2. Use a Jetson-specific wheel source selected by the user or their platform documentation.

Do not promise that a generic manylinux aarch64 CUDA wheel will run on Jetson.

## Unsafe Installer Script Policy

Legacy CUDA installer helper scripts that download or install CUDA are reference-only for this skill. Do not run them automatically. Prefer these safer steps:

1. Identify the runtime PyTorch reports.
2. Identify the native library bitsandbytes tries to load.
3. Decide whether a compatible wheel exists.
4. If source build is needed, give backend-specific CMake commands and ask the user to confirm any system package, driver, or toolkit changes.

## Post-Build Checks

Run read-only import and diagnostic checks first:

```bash
python -c "import bitsandbytes, torch; print(bitsandbytes.__version__, torch.__version__, torch.version.cuda, torch.version.hip)"
python -m bitsandbytes
python sub-skills/installation-diagnostics/scripts/backend-report.py --json
```

Only run accelerator kernel smoke tests after confirming hardware availability. A CUDA optimizer smoke test that creates `.cuda()` tensors is invalid in CPU-only CI and should not be used as a general install check.
