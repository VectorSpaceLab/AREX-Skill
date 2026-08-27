# OpenMC cross-cutting troubleshooting

Read this reference when a failure could belong to more than one workflow. The
nearest sub-skill owns detailed recovery; use the route links rather than
repeating the same diagnosis.

## Separate the gates

| Symptom | First distinction | Next action |
|---|---|---|
| `ModuleNotFoundError`, dependency import error, or version mismatch | Base Python/API gate failed | Read [setup-runtime](../sub-skills/setup-runtime/SKILL.md); inspect the environment with its read-only helper and confirm the installed distribution/version. |
| `import openmc` works but `openmc` executable is missing | Python package is not a native transport build | Read setup-runtime's build and execution references; configure an out-of-source CMake build and check the resulting executable explicitly. |
| `import openmc` works but `import openmc.lib` raises an `OSError` for `libopenmc.so` | Native shared-library gate failed, not necessarily the Python gate | Read [advanced-solvers](../sub-skills/advanced-solvers/SKILL.md); check the library path/loader dependencies and build options. |
| Run stops with no cross-section file or missing nuclide data | Data gate failed before physics interpretation | Read [nuclear-data-depletion](../sub-skills/nuclear-data-depletion/SKILL.md); validate the explicit `cross_sections.xml` and all referenced HDF5 files. |
| XML parses but model validation fails | Input graph/configuration issue | Read [model-geometry](../sub-skills/model-geometry/SKILL.md); inspect IDs, fills, regions, lattice shape, source, and settings. |
| Statepoint/tally/summary cannot be opened or has wrong shape | Output contract or run provenance issue | Read [tallies-results](../sub-skills/tallies-results/SKILL.md); inspect file type, batch/score/filter metadata, and autolink paths. |
| An optional feature is requested but unavailable | Native build/dependency gate is unknown or off | Read advanced-solvers; report the exact CMake feature and external prerequisite rather than silently falling back. |

## Safe diagnosis sequence

1. Record the package version, Python version, executable/library path, working
   directory, data-index path, energy/run mode, and the exact error fragment.
2. Run only read-only checks first. The setup-runtime and advanced-solvers
   helpers report package/native/data status without downloading, compiling, or
   running a user model.
3. Validate XML and HDF5 paths before changing geometry or physics settings.
4. Reduce to an XML-only model/API check, then a bounded native smoke, then the
   smallest data-backed run. Do not use a successful XML export as evidence of a
   successful transport calculation.
5. Preserve generated XML, logs, and result metadata in a task-specific output
   directory. Do not overwrite reference outputs while diagnosing.

## Frequent recovery boundaries

- **Missing `cross_sections.xml`:** locate or explicitly configure a compatible
  library; do not embed a machine-specific path in a reusable model. The
  index's relative `<directory>` and library paths are resolved from the index
  location by the bundled validators.
- **Missing HDF5 referenced by the index:** repair the data installation or
  index paths. Do not change nuclide names, temperatures, or model geometry as a
  first response.
- **Native library loader error:** inspect whether `libopenmc` was built,
  whether its loader dependencies are visible, and whether the Python binding
  points at the matching build. Rebuild or adjust the native installation only
  in a controlled environment.
- **MPI/optional integration failure:** check compiler/runtime and CMake cache;
  a host may have a Python package but no MPI, MOAB, DAGMC, libMesh, or NCrystal
  support. Mark that capability unverified until a feature-specific smoke passes.
- **Nondeterministic test differences:** bound OpenMP threads, use the native
  strict-floating-point option when reference comparison requires it, and
  compare the same particle/batch/seed configuration. Do not widen tolerances
  before checking the run configuration.
- **No reproducible result:** verify the model XML/configuration hash, particle
  seed, active/inactive batches, source, cross-section index, OpenMC revision,
  and output artifact type before comparing physics values.

## Stop conditions

Stop and ask for the missing input or authorization when the next step needs a
large external nuclear-data download, credentials, an unavailable backend or
system library, destructive replacement of an existing environment/build, or a
long transport/depletion/regression run. Record the exact blocked gate and the
smallest viable next action.
