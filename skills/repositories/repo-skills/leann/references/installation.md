# Installation and environment selection

Read this before choosing a LEANN package set or diagnosing an import. LEANN is
a Python 3.10+ monorepo with a core distribution and separately discovered
backend distributions.

## Choose the installation context

### Package user

The public meta-package installs core plus the default CPU backend set:

```bash
python -m pip install leann
python -c "from leann import LeannBuilder, LeannSearcher, LeannChat; print('LEANN import OK')"
```

At the provenance snapshot, `leann` depends on `leann-core`,
`leann-backend-hnsw`, `leann-backend-diskann`, and `leann-backend-ivf`. Treat
that as a package-resolution contract, not proof that every native backend can
load on the current platform.

For a deliberately smaller CPU environment, install the core and only the
backend distributions required by the workload, for example:

```bash
python -m pip install 'leann-core[cpu]' leann-backend-hnsw leann-backend-ivf
```

The Linux `cpu` extra pins a CPU-compatible Torch variant on supported Python
versions. Verify the resolver result rather than layering it over an unrelated
CUDA environment.

The HTTP service requires the core server extra:

```bash
python -m pip install 'leann-core[server]'
```

Install that alongside the selected backend distribution. MCP stdio entry
points are supplied by core; client integration details live in the MCP
sub-skill.

### Repository developer

Use the repository's `uv` workspace and initialize only the submodules required
by the package being changed. Do not use editable source builds as the default
answer to an ordinary package-user issue. Read the development sub-skill for OS
libraries, focused tests, package-version checks, and guarded wheel/release
work.

## Distribution, import, and registry names

| Role | Distribution/import | Registry name |
|---|---|---|
| Core API and CLI | `leann-core` / `leann` | n/a |
| HNSW | `leann-backend-hnsw` / `leann_backend_hnsw` | `hnsw` |
| CPU IVF | `leann-backend-ivf` / `leann_backend_ivf` | `ivf` |
| DiskANN | `leann-backend-diskann` / `leann_backend_diskann` | `diskann` |
| CUDA exact FlashLib | `leann-backend-flashlib` / `leann_backend_flashlib` | `flashlib` |
| CUDA IVF FlashLib | `leann-backend-flashlib-ivf` / `leann_backend_flashlib_ivf` | `flashlib-ivf` |

Backend autodiscovery scans installed distributions named `leann-backend-*` and
imports the corresponding underscore module. A distribution can be installed
yet absent from the registry when its optional/native import fails.

## Backend selection at install time

- Start with HNSW for the default compact local-search path.
- Add IVF when in-place add/remove/modify workflows matter.
- Add DiskANN only when its larger-than-memory/partition path is selected and
  the native package can be built or installed on the target platform.
- Install FlashLib variants only after choosing a CUDA-compatible Torch,
  FlashLib wheel/source, driver, and device combination. A visible NVIDIA GPU
  alone is not compatibility proof.
- MLX/MPS embedding support is Apple-Silicon-specific and does not replace a
  vector backend distribution.

Do not install all backend packages to make autodiscovery errors disappear.
Choose the backend first, then verify its import and a task-relevant tiny smoke.

## Minimal offline verification

Use the bundled probe from any working directory:

```bash
python /path/to/leann-skill/scripts/check_leann_install.py --check-cli
python /path/to/leann-skill/scripts/check_leann_install.py --require-backend hnsw
```

It does not load a model, contact a provider, start a daemon, or create an
index. For an end-to-end no-download HNSW fixture, use the API sub-skill's
precomputed-index smoke only after the import/backend probe passes.

## Native source-build prerequisites

HNSW source builds use CMake/SWIG and bundled FAISS, msgpack-c, and cppzmq
submodules. Linux builds also need discoverable ZeroMQ, OpenMP, BLAS, and
LAPACK. Diagnose the first missing CMake target rather than adding broad system
packages blindly. If CMake finds ZeroMQ but not BLAS, identify the actual
manager-owned BLAS/LAPACK libraries and pass explicit CMake paths for that
environment.

DiskANN and accelerator builds have their own compiler/runtime constraints.
Use their focused backend reference and preserve optional-backend status when a
native build is not required by the task.

## Version and ABI checks

```bash
python -m pip check
python -c "import torch, numpy; print(torch.__version__, numpy.__version__)"
python scripts/check_leann_install.py --json
```

A successful install command is not enough. Check component versions, native
imports, backend registry entries, and CLI parser construction. If Torch or a
native extension warns about a NumPy ABI generation mismatch, install a
mutually compatible set instead of suppressing the warning.
