---
name: platforms-performance
description: "Select and diagnose OpenMM runtime platforms, platformProperties,
  GPU/CPU precision modes, plugin availability, and safe performance tuning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT, GPL, LGPL
---

# Platforms and Performance

Use this sub-skill when the user needs to choose or troubleshoot an OpenMM `Platform`, configure `platformProperties`, verify GPU/CPU availability, or reason about performance diagnostics. Keep production simulation construction in `simulation-workflows`, force-field/system modeling in `force-fields-modeling`, custom force or integrator authoring in `custom-forces-integrators`, and new platform/kernel development in `development-extensions`.

## Quick Routing

- For listing installed platforms, checking package/plugin availability, or verifying a small Context can run, use `scripts/check_openmm_platforms.py` and the troubleshooting guide.
- For choosing `Reference`, `CPU`, `CUDA`, `OpenCL`, or `HIP`, and setting `Simulation(..., platform=..., platformProperties=...)`, read `references/platform-selection.md`.
- For precision, device selection, CPU threads, determinism, first-run kernel compilation, benchmarks, and PME tuning caveats, read `references/performance-and-benchmarking.md`.
- For missing CUDA/OpenCL/HIP platforms, driver/package mismatches, plugin directory problems, unsupported properties, and nondeterministic results, read `references/troubleshooting.md`.

## Safe Defaults

- Prefer `CUDA` or `HIP` for supported GPUs, `OpenCL` when that is the available accelerator, `CPU` for multithreaded CPU runs, and `Reference` for correctness smoke tests or fallback diagnostics.
- For GPU production runs, start with `{"Precision": "mixed"}` unless the user explicitly prioritizes maximum throughput over energy conservation or needs full double precision.
- Always provide a graceful fallback path when selecting optional GPU platforms: list available platforms first, then choose the requested platform if present, otherwise fallback to `CPU` or `Reference` with a clear warning.
- Do not recommend long benchmarks as routine checks. Use benchmark scripts only as optional, user-approved performance studies after installation and simulation setup already work.

## Bundled Files

- `references/platform-selection.md`: platform inventory, selection examples, platform property matrix, and installation extras.
- `references/performance-and-benchmarking.md`: precision/performance tradeoffs, benchmark interpretation, PME tuning, and determinism notes.
- `references/troubleshooting.md`: symptom-oriented fixes for missing platforms, plugin loading, device selection, precision, and runtime performance issues.
- `scripts/check_openmm_platforms.py`: a lightweight diagnostic script adapted from OpenMM's installation test pattern for safe listing and optional smoke checks.
