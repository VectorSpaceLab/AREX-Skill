---
name: openmc
description: "Guide OpenMC Python and native Monte Carlo particle-transport
  workflows: install and build the runtime, construct models, prepare nuclear
  data and depletion, inspect tallies/results, and diagnose optional solver
  integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# OpenMC operating skill

Use this skill when a task mentions OpenMC, continuous-energy or multigroup
Monte Carlo transport, CSG reactor/fusion geometry, `cross_sections.xml`,
statepoint/tally files, depletion chains, MGXS, random ray, CMFD, or the
`openmc.lib` C API. This is a router, not a replacement for the detailed
workflow references.

## First classify the task

- **Install, compile, run XML inputs, configure data paths, OpenMP/MPI, or
  diagnose an executable/library failure:** read
  [setup-runtime](sub-skills/setup-runtime/SKILL.md).
- **Build materials, surfaces/regions/cells/universes/lattices, sources,
  settings, plots, or XML-only models:** read
  [model-geometry](sub-skills/model-geometry/SKILL.md).
- **Create filters/tallies or inspect statepoint, summary, track, restart, and
  plot output:** read [tallies-results](sub-skills/tallies-results/SKILL.md).
- **Validate cross-section/chain files, process ENDF/ACE/HDF5, use MGXS/MicroXS,
  or run depletion/decay/R2S:** read
  [nuclear-data-depletion](sub-skills/nuclear-data-depletion/SKILL.md).
- **Use random ray, CMFD, weight windows, C API/library mode, C++/CTest, DAGMC,
  libMesh, NCrystal, or other optional native integrations:** read
  [advanced-solvers](sub-skills/advanced-solvers/SKILL.md).

For a request spanning routes, establish setup/data gates first, construct the
model next, then run transport and inspect outputs. Do not route an output-file
problem to model construction merely because the model created the file.

## Honest readiness gates

Report the gates separately:

1. `import openmc` and the base Python dependencies work.
2. An `openmc` executable is available for transport and subprocess workflows.
3. `import openmc.lib` loads a compiled shared library for C API/library mode.
4. `cross_sections.xml` parses and every referenced data file exists and is
   compatible with the requested energy mode.
5. Optional MPI/DAGMC/libMesh/NCrystal/strict-FP features are enabled and
   verified in the native build.

An XML export proves only Python model serialization. It does not prove a
transport run, native library, cross-section coverage, or tally correctness.
Use [troubleshooting](references/troubleshooting.md) when a gate is ambiguous.

## Minimal package check

For a supported Python environment, install the public package and its focused
test tools as needed, then run:

```bash
python -m pip install openmc
python -c "import openmc; print(openmc.__version__)"
```

A source build is a separate CMake workflow; read `setup-runtime` before
assuming that a Python install supplies the executable or `libopenmc`.
Avoid downloading nuclear data or changing shell startup files without explicit
user approval. Keep data and generated inputs in a dedicated working directory.

## Shared operating rules

- Capture the OpenMC version, run mode, energy mode, particle type, data index,
  executable/library paths, and output directory before changing a workflow.
- Prefer small API/XML checks and bounded unit tests before transport,
  depletion, or full regression suites. Follow the repository's test guidance
  for `OMP_NUM_THREADS` and strict reproducibility when comparing results.
- Use explicit `Path` values and validate XML/HDF5 inputs before interpreting a
  physics or geometry error. Keep missing data, missing native artifacts, and
  invalid model inputs as distinct diagnoses.
- Never claim MPI, GPU, DAGMC, libMesh, NCrystal, or C API support from a Python
  import alone. Optional features are verified only by their native build and a
  safe feature-specific check.
- If the source checkout or package version has changed, read
  [repo-provenance.md](references/repo-provenance.md) and use a refresh workflow
  rather than silently relying on stale operating knowledge.

## Common references

- Read [troubleshooting.md](references/troubleshooting.md) for cross-cutting
  install/import, data/config, CLI/API, native-build, and result-file failures.
- Read [testing-and-verification.md](references/testing-and-verification.md) for
  bounded native-test selection, data-dependent gates, and result expectations.
- Read [repo-provenance.md](references/repo-provenance.md) before a refresh or
  when reconciling a skill claim with a different OpenMC revision.
