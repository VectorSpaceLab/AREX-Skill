# Backend Compatibility

Use this reference to decide whether a `bitsandbytes` install should work from a wheel, needs a matching PyTorch accelerator build, or should move to a source build.

## Baseline Requirements

| Requirement | Current expectation |
| --- | --- |
| Python | 3.10 or newer for most platforms; Windows ARM64 requires 3.12 or newer. |
| PyTorch | 2.4 or newer baseline. XPU and HPU require newer backend-specific PyTorch stacks. |
| Package install | `pip install bitsandbytes` is the normal first attempt. |
| Diagnostic CLI | `python -m bitsandbytes` prints platform, Python, PyTorch, accelerator runtime, related package versions, and selected backend diagnostics. |
| CPU-only inspection | `import bitsandbytes` and API/signature inspection can be valid without GPU kernels; do not promise accelerator ops in CPU-only PyTorch. |

## Platform and Backend Matrix

| Backend | Wheel support and minimums | Notes for diagnosis |
| --- | --- | --- |
| CPU | Linux x86-64/aarch64, Windows x86-64/ARM64, and macOS arm64 wheels exist. Linux requires glibc 2.24+. x86-64 CPU wheels expect AVX2; Windows ARM64 expects ARM NEON. | CPU wheels can support import and CPU implementations, but CUDA/ROCm native methods are unavailable. If a native method says it is not available in CPU-only bitsandbytes, the wrong backend is being exercised. |
| NVIDIA CUDA | NVIDIA GPUs with compute capability 6.0+ are the practical minimum. LLM.int8 tensor-core paths need 7.5+ for fast support; 8-bit optimizers and NF4/FP4 need 6.0+. CUDA Toolkit 11.8 through 13.0 are supported for builds. | The loaded binary name is based on PyTorch's `torch.version.cuda` unless `BNB_CUDA_VERSION` overrides it. CUDA 13 wheels target newer SMs and drop older pre-Turing targets. |
| AMD ROCm | Preview support. Requires ROCm-enabled PyTorch. Linux and Windows wheels are built for selected ROCm versions and gfx targets. Source builds support HIP with `COMPUTE_BACKEND=hip`. | PyTorch reports ROCm via `torch.version.hip`; bitsandbytes chooses `libbitsandbytes_rocm{major}{minor}` unless `BNB_ROCM_VERSION` overrides it. |
| Intel XPU | Requires PyTorch with Intel XPU support; minimum PyTorch is 2.6.0. Wheels use SYCL plus Triton kernels on Linux/Windows x86-64. | `torch._C._has_xpu` selects `libbitsandbytes_xpu`. Verify that the PyTorch package is an XPU build before debugging bitsandbytes itself. |
| Intel Gaudi HPU | Requires a compatible Gaudi stack; current minimum is Gaudi v1.21 with PyTorch 2.6.0. | HPU support is not equivalent to CUDA. 8-bit optimizers may be unsupported even when some quantization paths are present. |
| Apple MPS / macOS arm64 | macOS 14+ arm64 wheels exist for CPU/MPS-related support; source builds can select `COMPUTE_BACKEND=mps` on Apple systems. | CUDA and HIP builds are not valid on macOS. Do not suggest CUDA toolkits for Apple Silicon. |
| Jetson / NVIDIA aarch64 L4T | Generic Linux aarch64 CUDA wheels target server-class ARM and are not compatible with Jetson L4T/JetPack CUDA libraries. | Recommend an on-device source build with explicit compute capability or a Jetson-specific third-party wheel source chosen by the user. Do not treat generic aarch64 CUDA wheels as sufficient for Jetson. |

## CUDA Wheel Build Coverage

Current CUDA wheels encode the CUDA runtime in the native library filename, for example `libbitsandbytes_cuda128.so` for CUDA 12.8 on Linux or `libbitsandbytes_cuda130.dll` for CUDA 13.0 on Windows.

| OS / architecture | CUDA toolkit range | Typical targets |
| --- | --- | --- |
| Linux x86-64 | 11.8-12.6 | sm60, sm70, sm75, sm80, sm86, sm89, sm90 |
| Linux x86-64 | 12.8-12.9 | sm70, sm75, sm80, sm86, sm89, sm90, sm100, sm120 |
| Linux x86-64 | 13.0 | sm75, sm80, sm86, sm89, sm90, sm100, sm120 |
| Linux aarch64 | 11.8-12.6 | sm75, sm80, sm90 |
| Linux aarch64 | 12.8-13.0 | sm75, sm80, sm90, sm100, sm110, sm120, sm121 |
| Windows x86-64 | 11.8-12.6 | sm50, sm60, sm75, sm80, sm86, sm89, sm90 |
| Windows x86-64 | 12.8-12.9 | sm70, sm75, sm80, sm86, sm89, sm90, sm100, sm120 |
| Windows x86-64 | 13.0 | sm75, sm80, sm86, sm89, sm90, sm100, sm120 |

Linux CUDA wheels require glibc 2.24 or newer. If a GPU has a compute capability below the target set in the available wheel, expect `no kernel image available` or source-build requirements.

## ROCm Wheel Build Coverage

ROCm binary names use `libbitsandbytes_rocm{major}{minor}`, for example `libbitsandbytes_rocm72.so`.

| OS / architecture | ROCm versions | Targets |
| --- | --- | --- |
| Linux x86-64 | 6.2.4, 6.3.4 | CDNA gfx90a/gfx942; RDNA gfx1100/gfx1101/gfx1102/gfx1103 |
| Linux x86-64 | 6.4.4 | Adds RDNA gfx1150/gfx1151/gfx1152/gfx1153/gfx1200/gfx1201 |
| Linux x86-64 | 7.0.2, 7.1.1, 7.2.3 | CDNA gfx90a/gfx942/gfx950 plus listed RDNA gfx11/gfx12 targets |
| Windows x86-64 | 7.2.1 | RDNA gfx1100/gfx1101/gfx1102/gfx1150/gfx1151/gfx1200/gfx1201 |

If PyTorch reports ROCm 7.2, bitsandbytes expects a `rocm72` library unless `BNB_ROCM_VERSION` changes the requested filename. Match the PyTorch ROCm runtime, the available library, and the actual system ROCm runtime before recommending a rebuild.

## Binary Selection Rules

1. If `torch.version.hip` is set and CUDA is available through PyTorch, bitsandbytes treats the backend as ROCm and requests `libbitsandbytes_rocm{torch_hip_major}{torch_hip_minor}`.
2. Else if `torch.cuda.is_available()` is true and `torch.version.cuda` is set, it requests `libbitsandbytes_cuda{torch_cuda_major}{torch_cuda_minor}`.
3. Else if `torch._C._has_xpu` is true, it requests `libbitsandbytes_xpu`.
4. Otherwise it attempts the CPU library.
5. `BNB_CUDA_VERSION` can override the CUDA filename suffix only for CUDA builds. `BNB_ROCM_VERSION` can override the ROCm filename suffix only for ROCm builds. Setting a ROCm override in a CUDA environment, or a CUDA override in a ROCm environment, is an error unless the matching override also exists and the other variable is ignored.

## CPU-Only CI Decision Pattern

For CI jobs that only inspect package metadata, imports, signatures, or documentation:

```bash
python -m pip install bitsandbytes torch --index-url <chosen torch index if needed>
python -c "import bitsandbytes, torch; print(bitsandbytes.__version__, torch.__version__, torch.cuda.is_available())"
python sub-skills/installation-diagnostics/scripts/backend-report.py --json
```

Acceptable result: import succeeds, versions print, `torch.cuda.is_available()` is false, and the report classifies the backend as CPU or CPU-only. Do not run legacy CUDA-only optimizer checks in CPU-only CI because they allocate CUDA tensors by design.

## Override Case Checklist

When a user set `BNB_CUDA_VERSION=130` and the package lacks `libbitsandbytes_cuda130`:

1. Read `torch.version.cuda` and `torch.cuda.is_available()`.
2. Read the override value and compute the requested library name.
3. List bundled `libbitsandbytes_cuda*` files from the installed package directory.
4. If `cuda130` is absent but the PyTorch default version has a bundled binary, recommend clearing `BNB_CUDA_VERSION`.
5. If neither requested nor default version is bundled, recommend installing a matching wheel/PyTorch pair or compiling from source with the target CUDA toolkit first on `PATH`.
6. Check `LD_LIBRARY_PATH` or platform equivalent only after the requested binary exists; a missing bitsandbytes binary and a missing CUDA runtime are different failures.
