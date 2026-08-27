# Repository provenance

Schema: `disco.repo-provenance.v1`

- Repository: FFCV (`https://github.com/libffcv/ffcv`)
- Source commit: `3a12966b3afe3a81733a732e633317d747bfaac7`
- Branch at extraction: `main`
- Exact tag: none reported at the source commit
- Source state at evidence snapshot: source checkout clean before generated
  skill/artifact files were added; generated output is intentionally local and
  unimported.
- Package metadata version: `1.0.1` from `setup.py`
- Module version: `1.0.2` from `ffcv.__version__`
- Native extension: `ffcv._libffcv`, built and imported during inspection
- Evidence roots: `ffcv/`, `libffcv/`, `setup.py`, `README.md`, `docs/`,
  `examples/docs_examples/`, `examples/cifar/`, and representative `tests/`
- Backend evidence: CPU synthetic writer/loader smoke passed; a tiny CUDA
  allocation passed on an A100 with compute capability 8.0. Full CUDA native
  suites and benchmark-scale/training runs were not part of routine evidence.

Refresh this skill when public APIs, field format version, native build logic,
install dependencies, cache/order behavior, or documented workflows change.
