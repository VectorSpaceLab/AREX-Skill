# Installation Compatibility

## Purpose

Use this shared reference for public bitsandbytes installation prerequisites and backend support before routing to detailed installation diagnostics.

## Core Requirements

- Python 3.10 or newer.
- PyTorch 2.4 or newer for the base package.
- `numpy` and `packaging` from package metadata.
- Public install path: `pip install bitsandbytes`.

## Backend Summary

| Backend | Practical notes |
| --- | --- |
| CPU | Supported for current wheels on major platforms. CPU-only checks can validate imports and some construction paths, but not accelerator memory savings. |
| NVIDIA CUDA | Requires compatible PyTorch CUDA runtime, supported compute capability, and a matching bundled `libbitsandbytes_cuda*` library or source build. LLM.int8() recommends newer Turing-class or better hardware; 4-bit and optimizers have broader CUDA support. |
| AMD ROCm | Preview support; match PyTorch ROCm runtime with bundled `libbitsandbytes_rocm*` or build from source when needed. |
| Intel XPU | Requires a compatible PyTorch XPU stack and oneAPI/SYCL-capable environment. Paged XPU examples are hardware-specific. |
| Intel Gaudi HPU | Requires Habana/Gaudi PyTorch stack; feature coverage differs from CUDA. |
| Apple MPS | Experimental/slow paths are documented for some features; do not assume parity with CUDA. |

## Source Builds

Use source builds when a wheel lacks the needed native binary, platform, accelerator, compute capability, or ABI. Detailed source-build routing lives in `../sub-skills/installation-diagnostics/references/source-builds.md`.

## Legacy Installer Scripts

The source repository contains CUDA installer helpers, but this skill treats them as reference-only because installer scripts can download packages or mutate system CUDA state. Prefer package-manager installs, documented wheels, or explicit source-build commands in the installation diagnostics sub-skill.
