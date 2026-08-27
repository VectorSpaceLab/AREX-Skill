# Development Troubleshooting

## When to Read

Read this when an OpenMM maintainer workflow fails during CMake configuration, native tests, plugin loading, platform kernel registration, serialization, wrapper builds, or generated wrapper exposure.

## CMake Configuration and Build Issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Expected platform/plugin library is not built | The relevant `OPENMM_BUILD_*` option is off or a prerequisite platform option is off | Reconfigure with the owning option enabled, then rebuild from a clean enough build tree for CMake target discovery. |
| Tests are missing from `ctest -N` | `BUILD_TESTING` or a platform-specific test option is off, or the target was not built | Reconfigure with testing enabled, build the tests, then list tests before running a focused regex. |
| Link errors after toggling static/shared builds | Static/shared compile definitions or export macros are inconsistent | Match neighboring target properties and avoid mixing stale build artifacts from different build modes. |
| GPU platform tests are unavailable | Backend SDK/runtime or build option is missing | Run Reference/CPU tests first; only require CUDA/OpenCL/HIP tests when hardware/runtime and build support are available. |

## Python Wrapper Build Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Set OPENMM_INCLUDE_PATH to point to the include directory for OpenMM` | Wrapper build cannot find OpenMM headers | Set `OPENMM_INCLUDE_PATH` to the include directory from the matching installed or staged OpenMM build. |
| `Set OPENMM_LIB_PATH to point to the lib directory for OpenMM` | Wrapper build cannot find OpenMM libraries | Set `OPENMM_LIB_PATH` to the library directory from the same build/install used for headers. |
| Import succeeds but a new C++ API is absent in Python | Wrappers were not regenerated or generated outputs were not rebuilt | Regenerate wrappers from the maintainer pipeline, rebuild the Python package, and run a focused Python signature/import test. |
| Wrapper link errors mention debug libraries | Debug library naming or compiler mode mismatch | Use the same build type and library names for OpenMM and wrappers; avoid Windows debug-library wrapper builds because the build logic does not support them. |
| Runtime import finds a different OpenMM than the build under test | Python path or installed package shadows the local build | Inspect `openmm.__file__` and package version during debugging; avoid treating an installed package smoke test as proof of local source changes. |

## Plugin Registration and Load Order

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Plugin loads but feature is unavailable on a platform | `registerKernelFactories()` did not register the abstract kernel name on that platform | Check the factory registration key exactly matches `KernelInterface::Name()` and that platform lookup succeeds. |
| Plugin fails when an optional backend is absent | Backend lookup exception is not caught | For optional platform implementations, catch missing-platform exceptions and skip registration for that backend. |
| New platform cannot receive factories from another plugin | Platform registration happens too late or not through `registerPlatforms()` | Register new `Platform` objects in `registerPlatforms()`, not after kernel factory registration starts. |
| Tests work only with direct registration helpers | Test/static helper registration is present but plugin initializer exports are missing | Keep helper functions for static tests, but ensure dynamic plugin libraries still export `registerPlatforms()` and `registerKernelFactories()`. |

## Missing Platform Kernel Errors

Common symptom: `Context` creation or first force evaluation reports that a kernel is unavailable for the selected platform.

Likely causes:

- The public feature requests a kernel name that no factory registered.
- The factory registered the wrong kernel name string.
- The selected platform was built without that feature/plugin implementation.
- Plugin libraries were not loaded before `Context` creation.
- A backend-specific implementation exists, but the common or backend source was not added to the target.

Recovery:

1. Identify the abstract kernel interface requested by the `ForceImpl` or `Integrator`.
2. Confirm its `Name()` string is used in each platform’s `registerKernelFactory()` call.
3. Confirm the target platform/plugin build option is enabled and the library was built.
4. Confirm plugins are loaded before creating the `Context`.
5. Run the smallest matching Reference test before CPU/GPU tests.

## Serialization Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| XML serialization says no proxy exists | Proxy registration is missing | Add or fix `SerializationProxy::registerProxy(typeid(Class), new ClassProxy())` in the owning registration unit. |
| Deserialized object loses a field | `serialize()` or `deserialize()` omitted a property | Add the property and a round-trip assertion. Consider version handling for older XML. |
| Old XML no longer loads | Schema changed without compatibility logic | Add versioned deserialization defaults or migration logic where feasible. |
| Plugin class serializes in C++ test but not user workflow | Plugin serialization library or registration path differs from the test path | Verify plugin serialization registration is part of the dynamic or installed component users load. |

## Platform-Specific Test Selection

- If a Reference test fails, fix correctness before looking at optimized backends.
- If Reference passes but CPU fails, inspect CPU-specific data structures, vectorized code paths, and `copyParametersToContext()` behavior.
- If CUDA/OpenCL/HIP fail but Reference/CPU pass, inspect Common Compute macros, generated kernel source encoding, precision variants, backend context casts, and device vector layout.
- For OpenCL tests that accept platform/device indices, confirm the requested indices match the available runtime.
- For GPU double-precision failures, confirm the build option and hardware capability before treating the failure as a feature regression.

## ABI, Compiler, and Generated-Code Mismatches

Symptoms include unresolved symbols, extension import failures, or behavior differences between C++ and Python.

Recovery checklist:

- Rebuild from a clean build tree after changing public headers, CMake source lists, export macros, or generated wrappers.
- Use matching compiler families and C++ standard settings for core libraries and wrappers.
- Ensure generated files correspond to the same source revision as the compiled libraries.
- Check Windows export macros and static-library definitions when adding new public classes.
- Treat generated wrapper outputs as derived artifacts; fix generation inputs and rerun generation rather than hand-patching generated files.

## Source Script Decisions

- The CTest helper is reference-only because it depends on a configured build tree and native test executables.
- Wrapper generation helpers are reference-only because they depend on source metadata, generated Doxygen/XML inputs, staging directories, and maintainer build state.
- CI, packaging, and release automation are excluded from this sub-skill because they are maintainer/release-specific and can mutate external state or depend on credentials/services.
- No runtime script is bundled for this sub-skill because safe static layout inspection is already captured in the references, while executable checks require a user-provided checkout/build tree.
