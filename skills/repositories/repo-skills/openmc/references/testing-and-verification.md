# Testing and verification guidance

Use this reference to choose a bounded check without confusing package/API,
native, data, and physics evidence.

## Verification ladder

1. **Static/runtime inspection:** parse the generated skill links/scripts; in a
   clean supported Python environment run `import openmc`, print the version,
   inspect representative signatures, and run `python -m pip check`.
2. **Data-free API/XML checks:** construct a tiny model, export XML, parse the
   generated documents, and exercise pure-Python data/depletion readers with
   tiny fixtures. These checks do not require cross sections or transport.
3. **Native CPU checks:** configure/build the executable/shared library with
   explicit CMake options, then run the smallest C++ unit tests or a tiny model
   with a known compatible data library. Set `OMP_NUM_THREADS=2` for repository
   tests unless the task requires another setting.
4. **Data-backed regression:** select a focused regression case whose input
   files, reference data, particle count, mode, and OpenMC revision are known.
   Do not run the whole suite merely to validate a route.
5. **Optional integrations:** verify MPI, DAGMC, libMesh, NCrystal, random ray,
   CMFD, weight windows, or C API/library behavior only after their build flags,
   external dependencies, and relevant data are proven.

## Candidate selection

- Package/API/model candidates: material, geometry, cell, lattice, source,
  settings, model, executor, tally/filter, statepoint, summary, and data/deplete
  unit tests. Prefer a small selected subset with no transport side effects.
- XML-only examples: a minimal pin-cell or custom-source builder; assert XML
  roots, IDs, fills, source settings, and parseability.
- Transport candidates: a fixed-source/eigenvalue or model XML case only when a
  valid executable and cross-section library are explicitly available.
- Depletion candidates: transport-free chain/results checks first; coupled
  depletion only with the native library, executable, chain, cross sections,
  volumes, and a bounded timestep.
- Advanced candidates: C++ geometry/tally/ray tests, `openmc.lib` lifecycle,
  random-ray/CMFD/weight-window cases, and optional integrations only when their
  native prerequisites are present.

## What to capture

For each check record the command, OpenMC version/commit, environment/backend,
input and data paths (outside public skill content), output directory, exit
status, and the expected signal. Preserve skipped checks with their reason:
missing data, absent native build, optional dependency, unavailable hardware,
network/credential boundary, or excessive cost. A skipped optional case is not
a pass; a failed required CPU/API gate blocks publication.

## Reference comparison cautions

OpenMC regression outputs can depend on compilation flags, strict floating
point settings, OpenMP/MPI process layout, random seed, active/inactive batches,
source definition, cross-section data revision, and platform. Regenerate
reference artifacts only under the repository's explicit update workflow. Do not
change tolerances or reference files to hide a configuration mismatch.

## Minimal verification snippets

```bash
python -c "import openmc; print(openmc.__version__)"
python -m pip check
python -m pytest -q <caller-selected-focused-tests>
```

Use the caller's checkout and focused tests only when the task is explicitly a
repository-maintainer check. For package-operation tasks, use the bundled
model/XML fixture or a caller-supplied project. Source-repository paths are
verification evidence, not runtime dependencies of this generated skill.
