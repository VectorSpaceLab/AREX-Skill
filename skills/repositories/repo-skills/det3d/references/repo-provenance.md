# Repository Provenance

- project: Det3D
- distribution: det3d
- public repository: `https://github.com/poodarchu/Det3D`
- source commit: `230bb199fac38d55d1bb9372283070ded11cafd1`
- source branch: `master`
- exact tag: none observed
- source state: clean at inspection baseline before generated skill artifacts
- package version evidence: source `det3d/version.py` reports `1.0.rc0+5d4f2e9` in the inspected checkout; `setup.py` defines short version `1.0.rc0`
- evidence paths: `README.md`, `GETTING_STARTED.md`, `INSTALLATION.md`, `docs/`, `setup.py`, `setup.cfg`, `requirements.txt`, `det3d/`, `examples/`, `tools/`
- excluded source categories: generated/build/cache files, local production logs and tests, datasets/checkpoints, notebooks and optional GUI implementation internals, raw CUDA/C++ bodies, CI/release infrastructure

This skill is distilled from a legacy repository snapshot. Refresh it when
model registries, dataset schemas, CLI flags, CUDA extension declarations,
installation constraints, or the source commit change. The runtime skill is
self-contained and does not require the source checkout to remain available.
