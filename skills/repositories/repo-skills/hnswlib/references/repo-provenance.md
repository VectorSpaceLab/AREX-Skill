# Repository provenance

schema: `disco.repo-provenance.v1`

- repository: `hnswlib`
- package version: `0.9.0`
- source commit: `d9b3608c83d83b46c96e25088cb1d729b29dcfe9`
- branch: `master`
- exact tag: `v0.9.0`
- source VCS state: generated from a dirty checkout; the dirty state consists of
  the production `skills/` output and review artifacts created for this skill,
  not changes to the versioned package sources.
- remote URL: `https://github.com/nmslib/hnswlib`
- generated scope: public Python bindings and CPU C++11 header-only API; large
  benchmark/download, CI/release, plotting, and stress-only utilities excluded.

## Relative evidence baseline

- Public intent and installation: `README.md`, `ALGO_PARAMS.md`,
  `TESTING_RECALL.md`
- Python packaging/bindings: `pyproject.toml`, `setup.py`, `MANIFEST.in`,
  `python_bindings/bindings.cpp`, `python_bindings/__init__.py`
- C++ API/build: `hnswlib/*.h`, `CMakeLists.txt`, `Makefile`
- Python recipes: `examples/python/`
- C++ recipes: `examples/cpp/`
- Python behavior tests: `tests/python/`, `python_bindings/tests/`
- Selected C++ behavior tests: `tests/cpp/epsilon_search_test.cpp`,
  `tests/cpp/multivector_search_test.cpp`,
  `tests/cpp/searchKnnCloserFirst_test.cpp`,
  `tests/cpp/searchKnnWithFilter_test.cpp`, `tests/cpp/updates_test.cpp`,
  `tests/cpp/multiThreadLoad_test.cpp`, and
  `tests/cpp/multiThread_replace_test.cpp`

This skill intentionally contains distilled guidance and bundled bounded smoke
helpers rather than links to those source files. Refresh it when the source
commit, package behavior, public API, or selected workflow scope changes.
