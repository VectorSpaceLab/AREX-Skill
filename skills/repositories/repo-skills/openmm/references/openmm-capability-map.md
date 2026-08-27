# OpenMM Capability Map

Use this map to route broad or ambiguous OpenMM requests before opening a deeper sub-skill.

| User request | Primary owner | Supporting owner | First validation signal |
| --- | --- | --- | --- |
| "Run a simple OpenMM simulation from a PDB" | `simulation-workflows` | `force-fields-modeling`, `platforms-performance` | Imports succeed, topology/system particle counts match, 0-10 Reference/CPU steps complete. |
| "Load Amber/GROMACS/CHARMM/Tinker files" | `simulation-workflows` | `force-fields-modeling` | Correct app loader pairing and `createSystem()` path are selected. |
| "Fix `No template found for residue`" | `force-fields-modeling` | `simulation-workflows` | `ForceField.getUnmatchedResidues()` or template-matching diagnosis identifies residue, bonds, hydrogens, or XML mismatch. |
| "Add hydrogens, solvent, ions, or membrane" | `force-fields-modeling` | `simulation-workflows` | `Modeller` changes topology/positions as expected before `createSystem()`. |
| "Write a custom restraint or nonbonded expression" | `custom-forces-integrators` | `force-fields-modeling` | Reference-platform finite energy/force with explicit parameter records. |
| "Implement a custom integration algorithm" | `custom-forces-integrators` | `platforms-performance` | `CustomIntegrator` variables/steps compile and a tiny system advances deterministically enough for the chosen algorithm. |
| "Choose CUDA, OpenCL, HIP, CPU, or Reference" | `platforms-performance` | `simulation-workflows` | Platform listing shows the requested platform and a tiny `Context` can be created. |
| "Why is CUDA missing or slow?" | `platforms-performance` | `development-extensions` when source build/plugin work is involved | Package/plugin/driver/property diagnosis points to install extra, driver, device index, precision, or plugin directory. |
| "Add a new C++ Force, plugin, kernel, or serialization proxy" | `development-extensions` | `custom-forces-integrators`, `platforms-performance` | API/impl/kernel/serialization/wrapper/test touchpoints are identified before editing. |
| "Build OpenMM or run maintainer tests" | `development-extensions` | `platforms-performance` for hardware variants | Existing build tree, CMake options, and safe test subset are explicit. |

## Sub-skill Ownership

- `simulation-workflows`: owns application-layer scripts, input loaders, `Simulation`, integrators for normal workflows, reporters, minimization, stepping, checkpoint/state restart, and bounded run validation.
- `force-fields-modeling`: owns `ForceField`, `Modeller`, topology preparation, bundled XML choices, parameterized input formats, residue-template diagnosis, and ffxml authoring.
- `custom-forces-integrators`: owns `Custom*Force`, `CustomIntegrator`, force groups, parameter updates, expression syntax, tabulated functions, and custom-system validation.
- `platforms-performance`: owns runtime platform selection, platform properties, GPU/CPU packages, plugin availability, precision, determinism, benchmark interpretation, and performance diagnostics.
- `development-extensions`: owns OpenMM source-tree architecture, C++ APIs, kernel/plugin implementation, serialization, wrappers, CMake builds, and maintainer tests.

## Cross-skill Workflows

- A realistic simulation script often needs `force-fields-modeling` first for `System` creation, then `simulation-workflows` for `Simulation`, then `platforms-performance` for GPU/CPU properties.
- A custom force in a force-field XML file starts in `force-fields-modeling` for ffxml wiring, then moves to `custom-forces-integrators` for expression semantics and validation.
- A missing GPU platform is a `platforms-performance` problem unless the user is compiling OpenMM from source or adding a new platform, which moves to `development-extensions`.
- A new core force starts with `development-extensions`; use `custom-forces-integrators` only as conceptual evidence for expression-based prototypes.
