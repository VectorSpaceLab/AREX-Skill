# Development and Packaging Troubleshooting

Start by preserving the first failing command, full error, interpreter identity,
host/architecture, selected package, and `git status`. Do not immediately rerun
a broad build helper or change multiple dependency layers.

## Decision matrix

| Symptom | Likely cause | Safe diagnosis | Corrective direction / proof |
|---|---|---|---|
| `python` is older than 3.10, `uv` chooses another interpreter, or PEP 604 syntax fails | Wrong Python or manager/environment identity | `python --version`; `uv run python --version`; print `sys.executable` | Recreate/select a Python 3.10+ `uv` environment. Prove both shell and `uv run` use the intended interpreter. Do not patch syntax back to Python 3.9. |
| Native source directory is empty; CMake cannot find Faiss/msgpack/DiskANN files | Recorded submodule not initialized | `git submodule status`; leading `-` means uninitialized | `git submodule update --init --recursive`, then verify recorded SHAs. Do not copy vendor sources or track arbitrary upstream heads. |
| HNSW CMake says `PkgConfig` or `libzmq` not found | Missing `pkg-config`, ZeroMQ development files, or search path | `pkg-config --version`; `pkg-config --modversion libzmq`; inspect `PKG_CONFIG_PATH` | Install host ZeroMQ development package and `pkg-config`, or point `PKG_CONFIG_PATH` to the selected environment. The bundled `libzmq` submodule alone does not satisfy current CMake. Prove `pkg-config` resolves `libzmq` before rebuilding. |
| HNSW gets past ZeroMQ but Faiss/CMake cannot find BLAS or LAPACK | Math libraries absent or CMake cannot resolve their concrete files | `python -c "import numpy as n; n.show_config()"`; inspect environment/library-manager BLAS and LAPACK paths; read CMake's first find failure | Install an architecture-appropriate BLAS/LAPACK implementation. If discovery still fails, pass verified `BLAS_LIBRARIES` and `LAPACK_LIBRARIES` paths plus `CMAKE_PREFIX_PATH` in `CMAKE_ARGS`; never paste another machine's prefix. A prepared CPU build required this explicit step. |
| OpenMP/compiler/linker failure, `libomp` not found, or C++ runtime mismatch | Missing OpenMP, mixed compilers, wrong deployment target, or unresolved package-manager prefix | `cmake --version`; compiler `--version`; show `CMAKE_PREFIX_PATH`/`OpenMP_ROOT`; inspect linked-library error | Use one coherent host toolchain. macOS requires libomp and normally system clang in CI; Windows requires VS 2022 C++ plus vcpkg paths; Linux needs compiler/OpenMP development packages. Rebuild from clean package build output only after confirming target. |
| Import works in shell but fails in tests, or source edits are ignored | Editable/wheel/umbrella package ambiguity | print `sys.executable`, `leann.__file__`, and `importlib.metadata.version` values under the exact test command | Use an isolated environment. For source tests install intended editables; for artifact tests install only candidate wheels. Do not fix with a global `PYTHONPATH`. |
| `pip check` shows torch/NumPy or CPU/CUDA conflicts; import emits ABI warnings | Resolver mixed CPU and CUDA variants, or an older torch is paired with NumPy 2 | `python -m pip check`; print torch/NumPy versions and `torch.version.cuda`; `numpy.show_config()` | Recreate a single-purpose CPU or CUDA environment and install one coherent torch source/variant. A prepared CPU environment needed NumPy below 2 with torch 2.2.2. Never downgrade a shared environment blindly. |
| CUDA FlashLib test is missing/failed on CPU | Optional CUDA package/device is absent; CPU has no behavioral substitute | check `torch.cuda.is_available()`, installed FlashLib distributions, and direct backend import | Mark optional CUDA coverage skipped unless the change requires it; then use an authorized compatible CUDA environment. Do not treat IVF CPU parity as FlashLib proof. |
| MPS/MLX test fails on Linux or non-Apple hardware | Apple Silicon-only optional dependency/runtime | inspect OS/architecture and package markers | Skip with an explicit platform reason or test on Apple Silicon macOS. Do not force-install MLX on unsupported hosts. |
| Pytest collection fails on an app/provider module | Test imports an optional SDK, app dependency, or live-service bridge not supplied by the test group | collect one target with `pytest --collect-only`; inspect the missing top-level package and owning test; check markers | Install only the dependency required by the selected owned test, or deselect an unrelated optional suite. If the changed package should declare it, fix metadata and add a negative install test. Do not install every extra. |
| Integration/provider test hangs or reaches network | Live-service/credential test selected, proxy mismatch, or unmarked model download | inspect node markers and skip conditions; check whether Ollama/LM Studio/API/model cache was intentionally prepared | Stop the test, choose mocked/parser coverage, or obtain explicit network/service/credential authorization. Record model and cache when a live test is necessary. |
| Backend is installed but absent from registry | Autodiscovery swallowed an import failure, distribution name is not discoverable, or editable metadata is wrong | import the backend module directly; query installed distribution metadata; then inspect `get_registered_backends()` | Fix the direct import/metadata/native dependency first. Registry edits are not the first response. Prove direct import and registration in the same interpreter. |
| Version checker reports component skew or an exact core pin mismatch | Package `pyproject.toml` versions are not aligned, or a dependency points to another component version | run checker with `--json`; compare every reported file, version, and internal constraint | Treat as release gate. Propose exact metadata/source constant/lock/changelog changes, but do not run a bump helper without authorization. Rerun checker and CPU metadata tests after reviewed edits. |
| Installed `leann.__version__` disagrees with distribution metadata | Historical source constant diverged from package metadata or wrong import wins | compare `importlib.metadata.version('leann')`, `leann.__file__`, and `getattr(leann, '__version__', None)` | Determine which distribution owns the import, reconcile source constant during an authorized release patch, and test from a fresh wheel environment. |
| Command would run release/version/upload/Hugging Face helper | Request crossed a mutation/credential boundary | stop; list side effects, exact target, version/SHA, artifacts, credentials, and rollback limits | Ask for explicit stage-specific authorization. Never rely on a shell confirmation prompt or existing token. Prefer read-only checklist and artifact validation. |
| Changelog/roadmap/docs disagree with code or tests | Significant change omitted docs, stale prose remained, or aspirational roadmap was marked complete | compare behavior and active config with the self-contained policy in this skill; run link/style checks as appropriate | Append a dated changelog entry at the bottom for significant changes; update roadmap state and affected examples; preserve unresolved vision items. Do not edit history to hide stale guidance. |

## Native HNSW diagnostic sequence

A proven failure progression was: first `libzmq` discovery failed; after ZeroMQ
and `pkg-config` were available, BLAS discovery failed; after concrete
BLAS/LAPACK libraries were supplied, the Python 3.11 HNSW build and import
succeeded. Follow the same layered diagnosis rather than installing broad extras.

```bash
# 1. Source state
git submodule status

# 2. Build front end and compiler
python --version
cmake --version
swig -version
${CXX:-c++} --version

# 3. ZeroMQ discovery
pkg-config --version
pkg-config --modversion libzmq

# 4. Python/math environment
python -c "import numpy as n; print(n.__version__); n.show_config()"

# 5. Only after identifying real library files, supply generic placeholders
# CMAKE_ARGS="-DCMAKE_PREFIX_PATH=<manager-prefix> \
# -DBLAS_LIBRARIES=<actual-blas-library> \
# -DLAPACK_LIBRARIES=<actual-lapack-library>" \
# python -m pip install --no-deps <hnsw-package-source>
```

Do not copy the commented placeholders literally. Use paths proved on the current
host. `--no-deps` is appropriate only when the exact candidate core and build
requirements are already installed; otherwise it can conceal a dependency gap.
After build, prove direct import, registry presence, `pip check`, and the
deterministic HNSW test.

## Stale documentation hierarchy

When prose conflicts, use this order for development facts:

1. active package metadata and executable config;
2. current CI workflow and assertion-bearing tests;
3. current contributor policy;
4. older test README or examples.

Known examples of stale prose are references to a `test/` directory rather than
`tests/`, a 600-second timeout rather than the active 300 seconds, and Python 3.9
coverage despite the active Python 3.10 floor. Fix stale docs in the same change
when relevant; do not silently propagate them into a release checklist.

## Failure records

For reproducibility, record:

- exact command and exit status;
- first causal error, not only the final wrapper message;
- Python executable/version and package distribution versions;
- OS, architecture, compiler, CMake, and native library source;
- submodule status;
- CPU/CUDA/MPS backend and relevant device availability;
- selected pytest node/marker and whether it passed, skipped, failed collection,
  timed out, or crashed;
- remediation and the proof command that passed afterward.

Keep secrets, tokens, private paths, and complete environment dumps out of shared
logs and documentation.
