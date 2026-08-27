# DGL Repo Development Reference

## When To Read

Read this when editing the DGL repository itself, selecting focused native tests, or diagnosing source-build versus package-wheel behavior. Ordinary package usage should start from the root `SKILL.md` and sub-skills instead.

## Source Layout

- `python/dgl/`: main Python package and public API surface.
- `src/`, `include/`, `CMakeLists.txt`: core native library source and build configuration.
- `graphbolt/`, `python/dgl/graphbolt/`: GraphBolt native and Python components.
- `dgl_sparse/`, `python/dgl/sparse/`: DGL sparse native and Python components.
- `dglgo/`: DGL-Go CLI package, recipes, and pipeline generators.
- `docs/source/`: Sphinx docs, guide chapters, install/backend notes, API references.
- `examples/`: user workflows; many download data or run training and should be classified before execution.
- `tests/python/`, `tests/tools/`, `dglgo/tests/`: behavior evidence and native verification candidates.
- `tools/`: distributed partitioning, launch, migration, and verification utilities.
- `script/`: source build, development environment, docs, and test launch helpers.

## Source Build And Test Environment

DGL source development commonly requires:

1. Initialized submodules.
2. CMake and a C++17 compiler.
3. A Python version supported by the checkout.
4. A matching PyTorch version for GraphBolt, sparse, and tensoradapter native extensions.
5. `DGL_LIBRARY_PATH` or installed package data pointing at built `libdgl`.

The repo's `script/run_pytest.sh` sets `DGLBACKEND=pytorch`, `DGL_LIBRARY_PATH` to the build directory, and `PYTHONPATH` to package and test roots. Treat it as a maintainer reference, not a runtime skill dependency.

## Focused Native Test Selection

Prefer short, deterministic tests after the runtime skill is integrated:

- Graph APIs: selected tests from `tests/python/common/test_convert.py`, `test_heterograph*.py`, `test_batch-graph.py`, `test_subgraph.py`.
- Datasets/IO: selected tests from `tests/python/common/data/test_serialize.py`, local-only `test_data.py`, and CSV fixtures.
- Message passing/training: selected tests from `tests/python/common/function/test_basics.py`, `tests/python/pytorch/nn/test_nn.py`, and `tests/python/pytorch/sparse/` when sparse imports.
- Dataloading/GraphBolt: selected tests from `tests/python/common/dataloading/test_dataloader.py` and `tests/python/pytorch/graphbolt/` when GraphBolt imports.
- Distributed tools: parser/schema checks and tiny partition tests only; skip cluster launch and large partition verification by default.
- DGL-Go: config/recipe linting and CLI help/config generation when dependencies are installed; skip full training by default.

Skip or ask before running tests/examples that require network downloads, GPUs, distributed clusters, large datasets, long training, SSH, credentials, or destructive writes.

## Maintainer Editing Notes

- Keep framework-agnostic Python APIs separate from framework-specific backend code where possible.
- PyTorch-specific layers and optimizers live under `python/dgl/nn/pytorch/`, `python/dgl/optim/pytorch/`, and related backend modules.
- GraphBolt and sparse native libraries are tightly coupled to torch ABI; test import and tiny operations after changes.
- Docs examples often assume data downloads and should be converted into tiny local fixtures before using as verification.
- Distributed tool changes should preserve dry-run/preflight behavior and avoid destructive mutation in helpers.

## Verification Escalation

Use this order:

1. Static import/signature checks and bundled skill scripts.
2. Focused Python unit tests for the edited area.
3. Native examples only if they are short and deterministic.
4. Full source build, distributed launch, CUDA, or benchmark-scale checks only after explicit approval and environment readiness.
