# Repository Architecture

## When to Read

Read this before changing OpenMM internals, adding a compiled feature, deciding where a test belongs, or explaining how a public API request maps to platform kernels.

## Maintainer Map

| Area | What it owns | Development notes |
| --- | --- | --- |
| `openmmapi/include` and `openmmapi/src` | Public C++ API classes and their implementation-layer partners | Public classes include `System`, `Force`, `Integrator`, `Context`, and concrete forces/integrators. Internal headers include `ContextImpl`, `ForceImpl`, and feature-specific implementation classes. |
| `serialization/include` and `serialization/src` | XML serialization framework and proxies for serializable API objects | New serializable classes need a proxy, registration, and round-trip tests. Serialization compatibility is a user-facing contract. |
| `platforms/reference` | Reference platform implementation | Use as first correctness target for new kernels and as a baseline for platform tests. |
| `platforms/cpu` | Optimized CPU platform and CPU tests | CPU has its own kernels/factories and platform-specific tests. |
| `platforms/common` | Common Compute infrastructure shared by OpenCL/CUDA/HIP style platforms | Use for host/device code that should be shared across GPU-like platforms. |
| `platforms/cuda`, `platforms/opencl`, `platforms/hip` | Backend-specific platform glue, kernel factories, contexts, and tests | Device code is encoded into generated sources during the CMake build. Backend tests often have single/mixed/double precision variants. |
| `plugins/amoeba`, `plugins/drude`, `plugins/rpmd`, `plugins/cpupme` | Optional plugins, public plugin APIs, platform implementations, wrappers, serialization, and tests | Plugins are the best local models for adding feature libraries and platform-specific kernel factories. |
| `wrappers` and `wrappers/python` | Generated language wrappers and Python packaging | Python wrappers are generated from C++ API metadata and built against installed OpenMM headers/libs. |
| `tests` and platform/plugin `tests` directories | C++ native tests grouped by subsystem/platform | Test executables are registered through CMake and generally require a configured build tree. |

## Core Execution Model

OpenMM has a layered architecture:

1. Public API objects such as `System`, `Force`, `Integrator`, and `Context` define user-visible state and behavior but do not directly compute forces.
2. `Context` creates a `ContextImpl`. Each `Force` in the `System` creates a corresponding `ForceImpl` through `createImpl()`.
3. A `Platform` attaches platform-specific data to the `ContextImpl` and supplies abstract `Kernel` handles backed by concrete `KernelImpl` objects.
4. `KernelFactory` instances registered on a `Platform` create `KernelImpl` subclasses for named kernel interfaces.
5. Each `ForceImpl` initializes the kernels it needs and calls those kernels during `calcForcesAndEnergy()` or state-update hooks.
6. `Integrator` classes request integration kernels directly; there is no separate `IntegratorImpl` layer because each `Context` owns its own `Integrator`.

Use this chain to locate required edits. A new public force usually needs a public `Force` class, a `ForceImpl`, an abstract kernel interface, one or more concrete platform kernels, registration through platform/plugin factories, serialization support when the object is user-visible, and tests.

## Public API and Implementation Ownership

- Public API classes live in exported headers and should remain stable and documented. Any constructor, setter, getter, or parameter semantics can affect C++, Python, and serialized XML users.
- `Force::createImpl()` connects a public `Force` to its `ForceImpl`; if it is missing or returns the wrong type, `Context` creation fails.
- `ForceImpl::getKernelNames()`, `initialize()`, `calcForcesAndEnergy()`, `updateContextState()`, and `copyParametersToContext()` are common points to inspect for feature completeness.
- Kernel interface names are used as registry keys. A mismatch between the abstract kernel `Name()` and the factory registration produces missing-kernel errors at `Context` creation or first use.

## Serialization Ownership

The serialization framework serializes public API objects through `SerializationProxy` subclasses. A complete serializable feature normally includes:

- A proxy header and implementation under the serialization tree or the owning plugin’s serialization tree.
- A proxy name string that remains stable across versions.
- `serialize()` that writes all user-visible parameters and version markers when fields may evolve.
- `deserialize()` that reconstructs valid objects and handles older versions when compatibility is required.
- Registration code that calls `SerializationProxy::registerProxy(typeid(Class), new ClassProxy())`.
- Round-trip tests for default values, non-default parameters, tabulated/function-like children when relevant, and backwards-compatible fields.

## Python Wrapper Ownership

Python exposes the C++ API through generated wrappers and package code. For C++ API changes:

- Expect wrapper-generation inputs and generated files to change, not only Python package sources.
- Check whether plugin APIs such as Amoeba and Drude have separate wrapper generation steps.
- Wrapper builds require an installed or staged OpenMM include directory and library directory; missing paths are a build-environment issue, not a Python API design issue.
- If a public class is not exposed in Python after a C++ change, inspect wrapper generation coverage before patching Python package code by hand.

## Contribution-Safe Checklist

For a nontrivial new compiled feature, verify the plan covers:

- Public API and documentation semantics.
- `ForceImpl` or `Integrator` internal behavior.
- Abstract kernel interface and platform-specific kernel implementations.
- Plugin registration if the feature lives outside the core library.
- Serialization proxy and tests if objects must persist to XML.
- Python wrapper exposure and import tests when the API is public.
- C++ native tests, platform tests, and Python tests where relevant.
