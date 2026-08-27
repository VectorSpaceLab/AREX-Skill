# Platform Selection

OpenMM exposes runtime backends through `openmm.Platform`. The installed package determines which platforms are visible at runtime, so platform-sensitive code should inspect availability instead of assuming that a GPU backend exists.

## Listing Platforms

Use this pattern in user code before selecting an accelerator:

```python
from openmm import Platform

available = [Platform.getPlatform(i).getName() for i in range(Platform.getNumPlatforms())]
print(available)
```

For a reusable diagnostic, run the bundled script:

```bash
python scripts/check_openmm_platforms.py --list
```

Add `--smoke` to create a tiny Context on selected platforms and confirm they can compute an energy. The smoke test is intentionally small; it is not a benchmark and should not be treated as simulation validation.

## Choosing a Platform

Use `Platform.getPlatformByName(name)` and pass both `platform` and, when needed, `platformProperties` to `Simulation` or `Context` creation.

```python
from openmm import Platform
from openmm.app import Simulation

platform = Platform.getPlatformByName("CUDA")
properties = {"Precision": "mixed", "DeviceIndex": "0"}
simulation = Simulation(topology, system, integrator, platform, properties)
```

For robust scripts, prefer a fallback helper:

```python
from openmm import Platform

def choose_platform(preferred=("CUDA", "HIP", "OpenCL", "CPU", "Reference")):
    available = {Platform.getPlatform(i).getName(): Platform.getPlatform(i)
                 for i in range(Platform.getNumPlatforms())}
    for name in preferred:
        if name in available:
            return available[name]
    raise RuntimeError("No OpenMM platforms are available")
```

Use `Reference` to confirm API correctness and isolate platform-specific issues. Use `CPU` for portable multithreaded execution. Use `CUDA`, `HIP`, or `OpenCL` for accelerator-backed runs when the matching platform is installed and the system driver/runtime is compatible.

## Platform Property Matrix

| Platform | Common properties | Notes |
| --- | --- | --- |
| `Reference` | none normally needed | Written for clarity and correctness checks, not performance. Useful as a fallback or comparison platform. |
| `CPU` | `Threads` | If omitted, OpenMM uses `OPENMM_CPU_THREADS` when set; otherwise it uses logical CPU cores. Use this to avoid monopolizing a shared machine. |
| `CUDA` | `Precision`, `UseCpuPme`, `TempDirectory`, `DeviceIndex`, `UseBlockingSync`, `DeterministicForces` | Supports comma-separated `DeviceIndex` for multiple GPUs. `TempDirectory` controls runtime kernel-cache temporary files when auto-detection is insufficient. |
| `OpenCL` | `Precision`, `UseCpuPme`, `OpenCLPlatformIndex`, `DeviceIndex` | `OpenCLPlatformIndex` selects among multiple OpenCL implementations; `DeviceIndex` selects devices within the chosen implementation and can be comma-separated. |
| `HIP` | same as `CUDA` | Recommended accelerator path for supported AMD GPU setups where the HIP plugin is installed. |

Property names are case-sensitive. Property values are strings, for example `{"Precision": "mixed"}` or `{"Threads": "8"}`.

## Precision Modes

`CUDA`, `OpenCL`, and `HIP` support these `Precision` values:

- `single`: fastest, least accurate; forces and most calculations are single precision.
- `mixed`: forces are single precision while integration is double precision; usually the best production default.
- `double`: highest precision, often substantially slower and dependent on hardware support.

If a selected precision is unsupported by the device or backend, Context creation can fail. Fall back from `double` to `mixed`, or from GPU to `CPU`/`Reference`, only with an explicit warning because numerical behavior changes.

## Installation Extras and Backends

The base `pip install openmm` package includes `Reference`, `CPU`, and `OpenCL` platforms. GPU plugin extras are separate:

```bash
pip install "openmm[cuda12]"
pip install "openmm[cuda13]"
pip install "openmm[hip6]"
pip install "openmm[hip7]"
```

Conda-forge installs use the `openmm` package and can target CUDA compatibility through the `cuda-version` selector, for example:

```bash
conda install -c conda-forge openmm cuda-version=12
```

Modern GPU drivers are still required. Conda packages and pip extras provide OpenMM's plugin binaries, but they do not replace the system vendor driver stack.

## Multi-GPU Device Selection

For `CUDA` and `OpenCL`, a comma-separated `DeviceIndex` such as `"0,1"` asks OpenMM to split supported computations across multiple devices. Use this only after confirming that the backend sees the expected devices and that the workload benefits from multi-GPU execution. A single fast GPU can outperform a split run for small systems.
