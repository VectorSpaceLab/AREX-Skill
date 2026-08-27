# Repo Provenance

- Schema: `disco.repo-provenance.v1`

## Source Snapshot

- Repository: OpenMM
- Canonical skill id: `openmm`
- VCS: git
- Commit: `3153ffff84f59eb814173c7c945201c0e74f0646`
- Branch: `master`
- Exact tag: none recorded
- Remote URL: `https://github.com/openmm/openmm.git`
- Working tree state at generation: dirty because new `skills/` output files were being created; no pre-existing source modifications were detected before skill generation.

## Package Version Facts

- Repository metadata in `CMakeLists.txt` reported OpenMM version components `8.5.0`.
- The temporary inspection package used for live API checks reported installed distribution `openmm` version `8.5.2`.
- The version difference means this skill should be refreshed if future work depends on behavior introduced or removed between the source checkout and the inspected package. Core APIs used here are long-lived OpenMM surfaces confirmed by source, docs, examples, and tests.

## Evidence Paths

- Root metadata and docs: `README.md`, `CMakeLists.txt`, `CONTRIBUTING.md`, `wrappers/python/setup.py`.
- Python package and app layer: `wrappers/python/openmm/`, `wrappers/python/openmm/app/`, `wrappers/python/openmm/unit/`.
- User documentation: `docs-source/usersguide/`, especially application, library, theory, platform, and force-field chapters.
- Developer documentation: `docs-source/developerguide/`.
- Examples: `examples/README.md`, `examples/python-examples/`, `examples/cpp-examples/`, `examples/extras/`.
- Public C++ APIs and implementation evidence: `openmmapi/include/`, `openmmapi/src/`, `serialization/`, `platforms/`, `plugins/`.
- Behavior evidence and native candidates: `tests/`, `wrappers/python/tests/`, `serialization/tests/`, platform and plugin test directories.

## Excluded or De-prioritized Paths

- `libraries/`: vendored third-party code, not user-facing OpenMM workflow guidance.
- Generated/build/cache outputs such as `build/`, `dist/`, `__pycache__/`, and test caches.
- CI/release/packaging automation under `devtools/ci/`, packaging manifests, and hosted environment files, except as install/build clues.
- Benchmarks and GPU/platform stress tests as default runnable checks; they are evidence and optional native candidates only.
- Large fixtures and native tests that require a compiled build tree, specialized hardware, long runtime, or original checkout state.

## Refresh Triggers

Refresh this skill when OpenMM changes public Python/C++ APIs, bundled force-field data, platform install extras, plugin packaging, CMake build options, serialization behavior, example workflows, or maintainer test layout.
