---
name: hnswlib
description: "Use hnswlib 0.9.0 for CPU approximate nearest-neighbor search
  through its Python bindings or C++11 header-only API, including indexing,
  filtering, persistence, mutation, and recall checks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# hnswlib

Use this repo skill when a task needs `hnswlib` for approximate nearest-neighbor
(ANN) indexing, querying, filtering, persistence, updates, deletion/replacement,
parameter tuning, or exact-recall comparison. The source contract is hnswlib
0.9.0. It exposes a CPU-native Python extension and a header-only C++11 API; it
does not expose CUDA, ROCm, MPS, or a service/CLI.

## Route first

- For NumPy arrays, `hnswlib.Index`, `hnswlib.BFIndex`, `knn_query`, Python
  callbacks, pickle, or Python persistence, read
  [sub-skills/python-bindings/SKILL.md](sub-skills/python-bindings/SKILL.md).
- For C++ headers, `HierarchicalNSW`, `BruteforceSearch`, `searchKnn`, filters,
  stop conditions, multivector/epsilon search, CMake, or thread ownership,
  read [sub-skills/cpp-header-api/SKILL.md](sub-skills/cpp-header-api/SKILL.md).
- Read [references/installation.md](references/installation.md) before a source
  build or when an import/compiler failure is involved.
- Read [references/parameter-tuning.md](references/parameter-tuning.md) when
  choosing `M`, `ef_construction`, `ef`, capacity, or a recall target.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a
  failure spans installation, persistence, data validation, or concurrency.

## Shared operating contract

1. Identify the metric (`l2`, `ip`, or `cosine`), vector dimension, capacity,
   label type/policy, query `k`, target recall, and whether deletion, replacement,
   filtering, resizing, or persistence is required.
2. Prefer the public package install (`pip install hnswlib`) when a compatible
   wheel exists. A source build needs NumPy, pybind11, a C++11 compiler, and the
   platform's native threading/OpenMP handling; use the installation reference.
3. Keep `k <=` the eligible live population and set `ef >= k`. ANN quality and
   speed depend on both construction and search parameters; validate material
   recall claims against `BFIndex` or another exact oracle.
4. Treat index files as binary artifacts tied to compatible metric/dimension and
   a deliberate capacity. Set `ef` again after file-based loading because file
   persistence resets it to the default; pickle preserves Python index state.
5. Coordinate lifecycle phases. Do not overlap querying with adding, resizing,
   saving/loading, or destruction. Python filters should use one query thread;
   keep C++ spaces, filters, stop conditions, and buffers alive for each call.
6. Use temporary or application-owned paths and bounded fixtures for smoke checks.
   Do not run large BigANN/SIFT downloads, benchmark-scale tests, or stress suites
   as a default operating workflow.

## Minimum smoke checks

Python users should run the relevant bundled helper with `--help` and then a
small default invocation from an environment where `hnswlib` is installed:
`sub-skills/python-bindings/scripts/python_lifecycle_smoke.py`,
`python_filter_smoke.py`, `python_mutation_smoke.py`, or `python_pickle_smoke.py`.
C++ users should run
`sub-skills/cpp-header-api/scripts/run_cpp_smoke.sh --help`, then provide an
include root containing `hnswlib/hnswlib.h`.

## Provenance and scope

Read [references/repo-provenance.md](references/repo-provenance.md) when checking
whether this skill matches a repository revision. Read
[references/repo-routing-metadata.json](references/repo-routing-metadata.json)
only as structured routing metadata; it is not an API manual.
