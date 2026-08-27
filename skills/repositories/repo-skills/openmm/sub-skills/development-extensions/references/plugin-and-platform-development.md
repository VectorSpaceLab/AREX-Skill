# Plugin and Platform Development

## When to Read

Read this when adding a compiled OpenMM feature, creating or modifying a plugin, implementing platform kernels, adding serialization, or deciding whether a user-level custom force should become C++ code.

## Choosing the Extension Mechanism

- Use user-level `Custom*Force` and `CustomIntegrator` APIs for expression-based behavior that fits existing kernels and does not require new C++ classes.
- Add a core C++ API feature when the behavior must be part of the public OpenMM API, requires new state semantics, or must be available without an optional plugin.
- Add a plugin when the feature has optional public APIs and platform implementations that can live outside the core library. Existing plugin families show this pattern for specialized forces, integrators, serialization, wrappers, and platform kernels.
- Add or modify a platform implementation when an existing abstract kernel needs a Reference, CPU, CUDA, OpenCL, HIP, or Common Compute backend.

## New Force or Integrator Checklist

For a new compiled `Force`-like feature, plan these pieces before coding:

| Piece | Typical responsibility |
| --- | --- |
| Public API class | User-facing constructor, particles/parameters, getters/setters, `createImpl()`, documentation semantics. |
| Implementation class | Context-specific state, validation, kernel request list, initialization, force/energy calculation, parameter updates. |
| Abstract kernel interface | A `KernelImpl` subclass contract with a stable `Name()` used for factory registration. |
| Reference kernel | Correctness-first implementation and easiest platform test target. |
| CPU kernel | Optimized CPU path when the feature should work on the CPU platform. |
| Common Compute or backend kernels | Shared GPU-like implementation plus CUDA/OpenCL/HIP glue when applicable. |
| Serialization proxy | XML round-trip support for public objects that users can save/load. |
| Python wrapper exposure | Regenerated wrappers and Python tests for public APIs. |
| Tests | Unit tests for API validation, serialization, Reference behavior, and each implemented platform. |

For an `Integrator`-like feature, there may be no `IntegratorImpl`, but the integrator should still request named kernels and own context-specific simulation state directly.

## Plugin Registration Model

A plugin loaded by OpenMM must expose two C functions:

```cpp
extern "C" void registerPlatforms();
extern "C" void registerKernelFactories();
```

OpenMM calls `registerPlatforms()` for all loaded plugins before it calls `registerKernelFactories()` for any of them. This ordering lets one plugin define a `Platform` and another plugin add kernel factories to that platform without relying on library load order.

Use this pattern:

- New platform plugin: create the `Platform` subclass and call `Platform::registerPlatform()` in `registerPlatforms()`, then register that platform’s kernel factories.
- New force plugin for existing platforms: leave `registerPlatforms()` empty, then in `registerKernelFactories()` get each target platform by name and call `platform.registerKernelFactory(KernelInterface::Name(), factory)`.
- Optional backend support: catch the platform lookup exception when a backend platform is absent and return without failing the whole plugin load.
- Static-library or direct-test paths may expose helper registration functions such as `registerDrudeReferenceKernelFactories()` or backend-specific equivalents; these are for tests/static linking and should not replace plugin initializer exports.

## Platform Kernel Pattern

A concrete platform implementation usually includes:

1. A `KernelFactory` subclass with `createKernelImpl(std::string name, const Platform&, ContextImpl&)`.
2. `if` or dispatch logic for each supported abstract kernel `Name()`.
3. A concrete `KernelImpl` subclass that implements the abstract kernel’s virtual methods.
4. Platform-specific context access through `ContextImpl::getPlatformData()` or backend context classes.
5. CMake wiring for shared/static targets and test registration.

Reference platform kernels are easiest to reason about and should favor clarity over speed. CPU kernels use CPU-specific data structures and vectorization paths. CUDA/OpenCL/HIP implementations often split backend-specific factories and contexts from shared Common Compute kernel logic.

## Common Compute Guidance

Use Common Compute when the same algorithm should serve CUDA, OpenCL, and often HIP-like platforms.

Device-code conventions:

- Use OpenMM’s cross-backend macros such as `KERNEL`, `DEVICE`, `LOCAL`, `GLOBAL`, `RESTRICT`, `GLOBAL_ID`, `GLOBAL_SIZE`, `LOCAL_ID`, `LOCAL_SIZE`, `SYNC_THREADS`, and `ATOMIC_ADD` instead of raw CUDA/OpenCL syntax.
- Use vector types common to both OpenCL and CUDA: 2, 3, and 4 element vectors of `short`, `int`, `float`, and `double` where supported.
- Use CUDA-style `make_` constructors in common code; OpenMM provides equivalents for OpenCL compilation.
- Avoid vector swizzle notation in common code because it is not portable to CUDA.
- Use `mm_long` and `mm_ulong` for 64-bit integer device code portability.

Host-code conventions:

- Accept or store a `ComputeContext` rather than a CUDA/OpenCL-specific context in common kernels.
- Create device arrays as `ComputeArray`; accept arrays through `ArrayInterface` when writing reusable functions.
- Compile source through `ComputeContext::compileProgram()`, create kernels with `ComputeProgram::createKernel()`, set arguments, and execute through `ComputeKernel`.
- Avoid host arrays of 3-component vectors when layout matters; OpenCL and CUDA differ in `float3` size/alignment.

## Serialization Proxy Pattern

When a public class must serialize:

1. Add a `SerializationProxy` subclass with a stable proxy type name.
2. In `serialize()`, write every user-visible property needed to reconstruct the object. Include a version property if the schema may evolve.
3. In `deserialize()`, read required properties, supply defaults for older versions where compatibility requires it, and validate object invariants.
4. Register the proxy during serialization proxy registration for core or plugin-owned classes.
5. Add tests that serialize, deserialize, and compare all meaningful properties.

Common failure modes include forgetting to register the proxy, omitting a new field, changing proxy names, and failing to maintain deserialization of older serialized objects.

## CMake Ownership for Plugins and Platforms

Plugin and platform directories generally define their own targets, include paths, compile definitions, and tests, while the top-level CMake file decides whether the component is included. When adding a feature:

- Add headers to the correct API/include tree so installation and wrapper generation can see them.
- Add source files to the owning CMake target.
- Add backend directories conditionally behind existing platform/plugin build options.
- Preserve shared/static library compile definitions and Windows export macros.
- Add test executables through the same `ADD_TEST` pattern as neighboring tests.
- Keep CI/release packaging scripts out of ordinary feature implementation unless the change alters distribution artifacts.

## Hard Case Walkthrough: New Force with Serialization and Reference/CPU

A robust plan for a new `Force` should name edits in this order:

1. Public header and source for the `Force` class, including validation and `createImpl()`.
2. Internal `ForceImpl` header/source with kernel request and parameter update behavior.
3. Abstract kernel interface header with a unique `Name()` string.
4. Reference kernel factory registration and `Reference*Kernel` implementation.
5. CPU kernel factory registration and `Cpu*Kernel` implementation if CPU support is required.
6. Serialization proxy, registration, and `TestSerialize*` coverage.
7. CMake target source lists and install/include exposure.
8. Wrapper generation and Python tests for public API exposure.
9. Focused C++ tests for Reference first, then CPU, then optional GPU/common compute backends.

If any row is intentionally omitted, document the user-visible limitation. For example, a feature without a CPU kernel should fail clearly on the CPU platform rather than appearing to support all platforms.
