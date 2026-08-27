# Architecture and Packages

## Two different installation contexts

Do not mix these contexts:

1. **Package user:** installs the published `leann` distribution and uses the
   public `leann` import/CLI. Route ordinary installation to the LEANN root
   skill.
2. **Checkout developer:** works in the monorepo, where the root project,
   editable `uv` sources, component distributions, native submodules, tests,
   apps, and build workflows interact. This reference is for that context.

Python 3.10 or newer is required by the active workspace, core, umbrella, IVF,
and FlashLib metadata. The current continuous-integration build matrix starts at
Python 3.10. Older contributor text that mentions Python 3.9 is stale.

## Monorepo map and verified version snapshot

The table describes the package metadata inspected for this skill. Treat the
versions as a skew snapshot, not a permanent promise; run the bundled checker on
the checkout being changed.

| Path role | Distribution / import | Snapshot | Relationship and build boundary |
|---|---|---:|---|
| Repository root | `leann-workspace` | 0.1.0 | Development aggregator. Its version is workspace metadata and is not part of component lockstep. Root dependencies include `leann-core` and HNSW, and `tool.uv.sources` maps local core, HNSW, DiskANN, both FlashLib packages, and the AST chunker to editable paths. |
| Umbrella package | distribution `leann` | 0.3.8 | Published dependency bundle: core, HNSW, DiskANN, and IVF. Its `cpu` extra delegates to `leann-core[cpu]`. This distribution must not be confused with the core source directory that owns the public `leann` namespace. |
| Core | distribution `leann-core`; import `leann` | 0.3.8 | Public API, CLI, chat, registry, embedding, synchronization, and MCP entry points. Declares `leann` and `leann_mcp` console commands. Pure Python packaging, but importing core currently reaches HNSW functionality, so a checkout with only core may not prove the public import path. |
| HNSW backend | distribution `leann-backend-hnsw`; import `leann_backend_hnsw` | 0.3.8 | Native scikit-build/CMake package; pins `leann-core==0.3.8`; embeds modified Faiss/msgpack/cppzmq sources but finds the ZeroMQ library via `pkg-config`. |
| DiskANN backend | distribution `leann-backend-diskann`; import `leann_backend_diskann` | 0.3.8 | Native scikit-build/CMake package; pins `leann-core==0.3.8`; requires the DiskANN submodule and platform math/compiler dependencies. Its wrapper forces `USE_TCMALLOC=OFF`. |
| IVF backend | distribution `leann-backend-ivf`; import `leann_backend_ivf` | 0.3.6 | Python package backed by `faiss-cpu`; requires `leann-core>=0.3.6`. Optional `query-server` support adds HNSW, ZeroMQ, and msgpack. |
| FlashLib backend | distribution `leann-backend-flashlib`; import `leann_backend_flashlib` | 0.3.6 | Optional CUDA package using `flashlib` and torch; requires `leann-core>=0.3.6`. |
| FlashLib IVF backend | distribution `leann-backend-flashlib-ivf`; import `leann_backend_flashlib_ivf` | 0.3.6 | Optional CUDA IVF-Flat package using `flashlib` and torch; requires `leann-core>=0.3.6`. |

The snapshot therefore has component skew: core/HNSW/DiskANN/umbrella are
0.3.8, while IVF and both FlashLib distributions are 0.3.6. Do not state that
all installed LEANN distributions share one version. A prepared Python 3.11 CPU
environment successfully imported core 0.3.8, HNSW 0.3.8, and IVF 0.3.6 and
discovered `hnsw` and `ivf`; that proves this mixed set imported, not that it is
a valid release set.

The umbrella source also contains a historical `__version__` constant that can
diverge from its distribution metadata. Use `importlib.metadata.version(...)`
when checking installed distribution versions, and explicitly reconcile any
source version constants during release review. The bundled checker deliberately
uses package `pyproject.toml` metadata and does not treat the root workspace
version as a release component.

## Dependency direction

```text
leann-workspace (checkout tools/apps)
├── leann-core  ── owns import namespace `leann` and CLI entry points
├── leann-backend-hnsw ── exact core pin + native Faiss/ZeroMQ build
├── optional leann-backend-diskann ── exact core pin + native DiskANN build
├── optional leann-backend-flashlib* ── CUDA/torch
└── editable astchunk source

published leann umbrella
├── leann-core
├── leann-backend-hnsw
├── leann-backend-diskann
└── leann-backend-ivf
```

Backend discovery scans installed distribution names beginning with
`leann-backend-`, converts hyphens to underscores, imports them in sorted order,
and lets each backend register itself. An import may be caught and omitted by
autodiscovery; therefore, absence from the registry can mean either “not
installed” or “installed but failed to import.” Diagnose the direct backend
import before changing registry code.

## Submodule ownership

A recursive checkout contains:

- `packages/leann-backend-hnsw/third_party/faiss`
- `packages/leann-backend-hnsw/third_party/msgpack-c`
- `packages/leann-backend-hnsw/third_party/cppzmq`
- `packages/leann-backend-hnsw/third_party/libzmq`
- `packages/leann-backend-diskann/third_party/DiskANN`
- `packages/astchunk-leann`

HNSW's current CMake configuration uses the Faiss, msgpack-c, and cppzmq source
submodules but resolves the actual `libzmq` library through system/package-manager
`pkg-config`. Initializing a bundled `libzmq` directory alone does not satisfy
that check.

## Native build prerequisites

Use the package manager appropriate to the host; inspect availability before
installing host packages.

| Host | Baseline prerequisites evidenced by development/CI |
|---|---|
| Ubuntu/Debian x86_64 | C/C++ toolchain, CMake 3.24+, SWIG, OpenMP, Boost, Protobuf compiler/libraries, ZeroMQ, `pkg-config`, Abseil, asynchronous I/O libraries, `patchelf`, and BLAS/LAPACK (the CI build uses Intel oneMKL on x86_64). |
| Linux ARM64 | Same general toolchain, with OpenBLAS/LAPACK/LAPACKE instead of Intel oneMKL. HNSW defaults Faiss to generic ARM64 instructions; opt into SVE only for hardware that supports it. |
| macOS | CMake, libomp, Boost, Protobuf, ZeroMQ, and `pkg-config`; system clang is used in CI. Contributor setup may install LLVM and point `CC`/`CXX` to it, but do not mix compiler runtimes accidentally. |
| Windows | Visual Studio 2022 C++ workload, CMake, SWIG, `pkg-config`, NuGet, and vcpkg packages for ZeroMQ, OpenBLAS, LAPACK, Boost program options, and Protobuf. `CMAKE_PREFIX_PATH`, `PKG_CONFIG_PATH`, and `OPENBLAS_LIB` must resolve the selected vcpkg triplet. |

Native wheels are platform- and Python-ABI-specific. A successful editable core
install does not validate an HNSW or DiskANN extension, and a CPU build does not
validate CUDA FlashLib packages.

## Editable-install ambiguity

The root workspace, local component editables, an old wheel, and the umbrella
package can all affect the same environment. Before trusting a test, capture:

```bash
python -c "import importlib.metadata as m; print({n: m.version(n) for n in ['leann-core','leann-backend-hnsw','leann-backend-ivf'] if any(d.metadata.get('Name') == n for d in m.distributions())})"
python -c "import leann; print(leann.__file__)"
python -m pip check
```

If `leann.__file__` does not point to the intended checkout environment, rebuild
an isolated environment instead of adding `PYTHONPATH` shims. For wheel testing,
uninstall/editable ambiguity is best avoided by creating a fresh environment
and installing only the newly built artifacts plus their declared dependencies.
