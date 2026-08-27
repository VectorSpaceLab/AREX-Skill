# Performance and Benchmarking

OpenMM performance depends on the selected platform, precision mode, hardware, nonbonded method, system size, constraints, and whether kernels have already been compiled and cached. Treat benchmark numbers as environment-specific measurements, not portable guarantees.

## Practical Selection Defaults

- Start GPU production runs with `Precision="mixed"`; it usually improves energy conservation with only a modest speed cost compared with `single`.
- Use `single` only when the user accepts lower precision for throughput and has validation appropriate for the scientific goal.
- Use `double` for workflows that require high precision and for devices where double precision performance is acceptable.
- Use `CPU` with a `Threads` property when the user needs a predictable share of a CPU machine.
- Use `Reference` for correctness debugging and fallback smoke tests, not for performance expectations.

Example:

```python
from openmm import Platform
from openmm.app import Simulation

platform = Platform.getPlatformByName("CUDA")
properties = {
    "Precision": "mixed",
    "DeviceIndex": "0",
    "DeterministicForces": "true",  # only when reproducibility is worth a speed cost
}
simulation = Simulation(topology, system, integrator, platform, properties)
```

## CPU Threads

The `CPU` platform property `Threads` controls the number of CPU worker threads. If it is omitted, OpenMM first checks `OPENMM_CPU_THREADS`; if that is not set, it uses the number of logical CPU cores. On shared systems, set `Threads` explicitly to avoid saturating the host.

```python
platform = Platform.getPlatformByName("CPU")
properties = {"Threads": "4"}
```

## GPU Runtime Costs

The `CUDA`, `HIP`, and `OpenCL` platforms compile kernels at runtime. First Context creation or first energy/step calls can be much slower than steady-state execution. CUDA and HIP cache compiled kernels on disk when possible; if temp-directory detection fails or the default temp area is not writable, set `TempDirectory` for CUDA/HIP Context creation.

Do not benchmark first-step time as steady-state speed. Warm up the Context, step for a short initial interval, then time the simulation segment of interest.

## Determinism

Determinism is platform- and method-dependent. PME with `Reference`, `OpenCL`, and double-precision `CUDA` has documented deterministic behavior in some contexts, while single-precision `CUDA` and `CPU` PME can be nondeterministic. This behavior is not guaranteed forever. If reproducibility matters, test the exact platform, precision, method, driver, and OpenMM version in use.

For `CUDA` and `HIP`, `DeterministicForces="true"` requests deterministic force accumulation for relevant operations at a small performance cost. It is not a substitute for validating the whole simulation protocol.

## Benchmark Script Evidence

OpenMM's benchmark example measures `ns/day` for selected systems, platforms, constraints, precision modes, and ensembles. It can write JSON/YAML results and includes setup for multiple benchmark systems, including Amber benchmark data that may be downloaded. Because it can perform long runs, download data, and require GPUs, treat it as reference-only during skill verification and ask the user before running benchmark-scale workloads.

Safe use pattern for future agents:

- Treat OpenMM's benchmark example as source evidence for benchmark design, not as a runtime dependency of this skill.
- For user workflows, recreate the relevant benchmark logic in the user's own project only after confirming the target system, platform, precision, number of steps, and whether downloads or long GPU jobs are acceptable.
- Record hardware, OpenMM version, platform, precision, constraints, timestep, ensemble, and system name with any performance result.

## PME Tuning Caveats

OpenMM's PME tuning example explores cutoff distances and CPU-vs-GPU reciprocal-space calculation. It mutates the `System` cutoff and platform properties while timing many candidate configurations, then leaves the passed `system` and `properties` set to the recommended values. The idea is useful, but it is not a safe default diagnostic because it can be time-consuming and workload-specific.

Important details for agents to preserve when advising users:

- PME cutoff can be varied for Coulomb reciprocal/direct-space balance while maintaining the chosen Ewald error tolerance, but Lennard-Jones and model-specific considerations may impose lower cutoff limits.
- `UseCpuPme` can help or hurt depending on CPU/GPU balance and system size.
- Tune on the actual hardware and a representative system; do not copy another machine's best cutoff or `UseCpuPme` setting blindly.
- If using a helper modeled on PME tuning, make the mutation explicit and clone or serialize objects when the original system/integrator must be preserved.

## Interpreting Platform Comparisons

When comparing platforms, distinguish these questions:

- Availability: Does `Platform.getNumPlatforms()` list the backend?
- Functionality: Can a tiny Context compute energy/forces on that backend?
- Numerical agreement: Do platforms produce comparable energies/forces for the same system within expected tolerances?
- Performance: After warmup, how many steps per unit time does a representative system achieve?

A platform can be listed but fail Context creation because the driver, device, precision mode, temp directory, or plugin dependencies are unsuitable. Conversely, a tiny smoke test can pass while a production system still fails because it uses unsupported precision, too much memory, PME settings, or plugin-specific kernels.
