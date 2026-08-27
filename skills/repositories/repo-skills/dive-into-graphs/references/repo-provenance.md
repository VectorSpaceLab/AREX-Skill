# Repo Provenance

This generated repo skill is based on the DIG (Dive into Graphs) source tree inspected during creation.

## Source Snapshot

- Package/import identity: PyPI distribution `dive-into-graphs`, Python package `dig`.
- Package version from `dig.version.__version__`: `1.0.0`.
- Git commit: `21476b079c9226f38915dcd082b5c2ee0cddaac8`.
- Git branch: `dig-stable`.
- Exact tag: not recorded.
- Remote URL: omitted-private-or-unknown.
- Working tree state at creation: dirty because generated skill/log artifacts existed under `skills/`.
- Relative dirty paths observed: `skills/`.

## Evidence Paths

Runtime guidance was distilled from these relative source-evidence paths:

- `README.md`, `setup.py`, `setup.cfg`, `MANIFEST.in`, `docs/environment.yaml`.
- `docs/source/intro/installation.rst`, `docs/source/index.rst`.
- `docs/source/tutorials/graphdf.rst`, `docs/source/tutorials/sslgraph.rst`, `docs/source/tutorials/subgraphx.rst`, `docs/source/tutorials/threedgraph.rst`, `docs/source/tutorials/oodgraph.rst`, `docs/source/tutorials/fairgraph.rst`.
- `docs/source/ggraph/*.rst`, `docs/source/sslgraph/*.rst`, `docs/source/xgraph/*.rst`, `docs/source/3dgraph/*.rst`, `docs/source/ggraph3d/*.rst`, `docs/source/oodgraph/*.rst`, `docs/source/auggraph/*.rst`, `docs/source/fairgraph/*.rst`.
- `dig/ggraph/`, `dig/ggraph3D/`, `dig/sslgraph/`, `dig/xgraph/`, `dig/threedgraph/`, `dig/oodgraph/`, `dig/auggraph/`, `dig/fairgraph/`, `dig/lsgraph/`.
- `examples/ggraph/`, `examples/ggraph3D/`, `examples/sslgraph/`, `examples/xgraph/`, `examples/threedgraph/`, `examples/oodgraph/`, `examples/auggraph/`, `examples/fairgraph/`, `examples/lsgraph/`.
- `benchmarks/xgraph/`.
- `test/ggraph/`, `test/sslgraph/`, `test/xgraph/`, `test/threedgraph/`, `test/oodgraph/`.

## Verified Package Facts

During creation, the inspected package successfully imported the primary public modules for `ggraph`, `ggraph3D`, `sslgraph`, `xgraph`, `threedgraph`, `oodgraph`, `auggraph`, and `fairgraph`. The `dig.lsgraph.dataset` import raised `ModuleNotFoundError: No module named 'dig_ext'`, matching source evidence that large-scale loaders and async pools depend on a compiled `dig_ext` extension not packaged in the inspected tree.

The public runtime skill intentionally omits private inspection environment paths and local executable paths. Refresh this skill when the source commit, public APIs, dependency constraints, or CUDA/extension behavior changes.
