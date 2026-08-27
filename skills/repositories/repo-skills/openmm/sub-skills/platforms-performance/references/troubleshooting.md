# Platform Troubleshooting

Use this guide when OpenMM imports successfully but a platform is missing, Context creation fails, a GPU is not used, performance is unexpectedly poor, or platform results differ.

## Missing CUDA, HIP, or OpenCL Platform

First list platforms:

```bash
python scripts/check_openmm_platforms.py --list
```

If the requested backend is absent:

- Confirm the installed package includes the backend plugin. The base pip package includes `Reference`, `CPU`, and `OpenCL`; install `openmm[cuda12]`, `openmm[cuda13]`, `openmm[hip6]`, or `openmm[hip7]` for those plugin families.
- For conda-forge installs, ensure the selected `openmm` build matches the intended CUDA compatibility, for example with `cuda-version=12` when targeting CUDA 12-compatible drivers.
- Confirm the system vendor driver is installed and visible. OpenMM package extras do not replace NVIDIA or AMD driver installation.
- Check whether multiple Python environments are being confused. Run diagnostics with the same `python` executable that will run the simulation.

## Plugin Directory and Library Loading Issues

OpenMM platforms are registered by plugin libraries. If plugins are installed but not loading:

- Check import failure messages from `python -m openmm.testInstallation` or the bundled diagnostic script with `--smoke`.
- Avoid mixing package managers or incompatible OpenMM plugin package versions in one environment.
- If using a custom build or nonstandard installation, verify that OpenMM's plugin directory and shared libraries are discoverable by the process environment.
- Do not hard-code local plugin paths into reusable skill content or project templates; resolve them in the target environment.

## Driver and Runtime Mismatch

Symptoms include a platform being absent, Context creation failing, or errors mentioning CUDA/HIP/OpenCL device initialization.

Recommended response:

1. Identify the intended backend and installed package variant.
2. Confirm hardware and driver support outside OpenMM with the vendor's normal tooling when available.
3. Align the package variant with driver/runtime compatibility, such as the CUDA major version selected for the OpenMM package.
4. Re-run a list-only diagnostic before trying a smoke Context.

For NVIDIA GPUs, CUDA packages are not binary-compatible across all major versions. For AMD GPUs, HIP/ROCm availability and OS support matter; HIP extras are intended for non-Darwin x86_64 package targets.

## Unsupported Precision or Property

If Context creation fails after adding properties:

- Check property spelling and capitalization: examples include `Precision`, `DeviceIndex`, `UseCpuPme`, `Threads`, `TempDirectory`, `UseBlockingSync`, and `DeterministicForces`.
- Keep property values as strings, for example `{"Threads": "8"}` and `{"UseCpuPme": "true"}`.
- Do not pass GPU-only properties to `CPU` or `Reference`.
- If `Precision="double"` fails or is slow, try `mixed`; if `mixed` fails on a problematic accelerator, fallback to `CPU` or `Reference` with a warning.

## Device Index Problems

For `CUDA`, `HIP`, and `OpenCL`, `DeviceIndex` is zero-based in the order reported by the backend API. For OpenCL, `OpenCLPlatformIndex` chooses among OpenCL implementations before `DeviceIndex` chooses devices within that implementation.

Common mistakes:

- Assuming OS-visible GPU numbering matches OpenMM backend numbering.
- Passing an integer instead of a string in `platformProperties`.
- Using a multi-device string such as `"0,1"` on systems where one device is unavailable or unsuitable.

When diagnosing, start with no `DeviceIndex`, then try one explicit device at a time.

## CPU Threads and Host Contention

If a CPU run monopolizes the host or performs inconsistently:

- Set `OPENMM_CPU_THREADS` or pass `{"Threads": "N"}` to the `CPU` platform.
- Avoid comparing CPU and GPU timings while other heavy processes are running.
- Check that the simulation is actually using `CPU` rather than falling back to `Reference`.

## Slow First Step or First Context

A slow first Context is normal for `CUDA`, `HIP`, and `OpenCL` because kernels may compile at runtime. For CUDA/HIP, compiled kernels can be cached when a writable temp/cache location is available. If repeated first-run costs occur, check temp directory permissions or set `TempDirectory` for CUDA/HIP.

Do not conclude a platform is slow from first-step timing alone. Warm up before measuring.

## Platform-Specific Nondeterminism

Small numerical differences across platforms or repeats can be expected, especially with parallel reductions, PME, and single precision. If the user needs exact reproducibility:

- Use the same OpenMM version, platform, precision, hardware, driver, and property settings across runs.
- Consider `DeterministicForces="true"` on CUDA/HIP when applicable.
- Compare scientifically relevant observables, not just bitwise trajectories, unless bitwise behavior is a formal requirement.
- Use `Reference` or double precision as diagnostic comparisons, not necessarily as production replacements.

## Safe Diagnostic Escalation

Use diagnostics in this order:

1. `python scripts/check_openmm_platforms.py --list`
2. `python scripts/check_openmm_platforms.py --smoke --platform Reference`
3. `python scripts/check_openmm_platforms.py --smoke --platform CPU` or the requested GPU platform
4. A tiny user-system Context with the intended `platformProperties`
5. A representative warmed-up benchmark only after the user approves runtime cost

Stop at the first failing layer and fix that layer before changing simulation physics or production settings.
