# Installation reference

This reference records the verified installation facts for the Earth2Studio
`0.18.0a0` source snapshot. It is a routing aid, not a replacement for the
package metadata selected by the user. The base install is intentionally small:
core APIs and IO are present, while most model and data-source integrations are
optional.

## Safe installation sequence

The installation sub-skill never runs package managers on the user's behalf.
Give the command, explain its scope, and wait for the user to execute it.

### Choose the interpreter

The package metadata declares `Python >=3.11,<3.15`; Python 3.13 is the
recommended target. A GPU install also needs a PyTorch build whose CUDA runtime
matches the host driver/toolkit expectations. CUDA 13 is the current default
TOML target in this source line, but that does not make every CUDA/PyTorch/model
combination interchangeable.

A new uv project can be prepared with:

```bash
mkdir earth2studio-project
cd earth2studio-project
uv init --python=3.13
```

A Conda-managed environment should be limited to interpreter isolation, then
Earth2Studio should be installed with standard Python tooling:

```bash
conda create -n earth2studio python=3.13
conda activate earth2studio
pip install "earth2studio[<extra>,...]"
```

Use the equivalent `uv add` or `pip install` form for a released package:

```bash
uv add "earth2studio[<extra>,...]"
pip install "earth2studio[<extra>,...]"
```

For an approved source revision, preserve the extras in the project's VCS
requirement rather than silently mixing a source checkout with a released
extra. The exact release or revision is a release-management decision and must
be substituted by the user.

### Verify the base environment

Run in the same environment that will run the later workflow:

```bash
python -c "import earth2studio; print(earth2studio.__version__)"
python -c "import torch; print('torch', torch.__version__); print('cuda build', torch.version.cuda); print('cuda available', torch.cuda.is_available())"
python scripts/check_environment.py --json
```

With uv, use `uv run python ...` so the check resolves the project lockfile.
`--require-cuda` is meaningful only for a GPU task; CPU inspection should not
fail merely because CUDA is absent.

## Dependency-group decision table

These are the optional groups observed in the source metadata. The table is
representative routing information; it is not an exhaustive model catalog.

| Need | Extra(s) to consider | Important boundary |
| --- | --- | --- |
| Core package | none | Core APIs do not include most model/data extras. |
| Remote/GRIB/data connectors | `data` | Includes connectors such as `cdsapi`, ecCodes/cfgrib-related packages, raster/geo packages, and scientific utilities. Credentials and system libraries remain separate concerns. |
| Model perturbation | `perturbation` | Includes `torch-harmonics` and SciPy; CUDA/build fit still matters. |
| Statistics | `statistics` | Adds PhysicsNeMo; select only if statistics APIs are needed. |
| Utility transforms | `utils` | Adds SciPy and earth2grid. |
| PX forecast models | one targeted model extra | The model class and checkpoint prerequisites must be checked together. |
| DX diagnostics/downscaling | one targeted diagnostic extra | Some DX models use PhysicsNeMo, earth2grid, CuPy, or external tools. |
| DA | `da-interp`, `da-healda`, `da-stormcast`, or `da-cosmo` | Beta APIs; CUDA-13 CuPy is used and most variants also use cuDF. |

Observed targeted PX extras include `ace2`, `aifs`, `aifs2`, `aifsens`,
`aifs2ens`, `atlas`, `aurora`, `dlesym`, `dlwp`, `fcn`, `fcn3`, `fengwu`,
`fuxi`, `gencast`, `graphcast`, `interp-modafno`, `pangu`, `sfno`, `stormcast`,
`stormcast-conus`, `stormscope`, and `ucast`. Observed DX extras include
`cbottle`, `climatenet`, `corrdiff`, `cosmo`, `cyclone`, `derived`, `orbit`,
`precip-afno`, `precip-afno-v2`, `solarradiation-afno`, and `windgust-afno`.
Use the installed package metadata for the authoritative set and dependency
versions.

## Known extra constraints

Do not combine extras just because their names look related.

- uv declares conflicts among the AIFS family: `aifs`, `aifs2`, `aifsens`, and
  `aifs2ens`. Select the one model line needed by the task.
- uv also declares `ace2` conflicts with `atlas`, `fcn3`, `perturbation`, and
  `sfno`. Put incompatible experiments in separate environments.
- `flash-attn`, `natten`, `torch-harmonics`, and `earth2grid` are configured as
  no-build-isolation-sensitive packages in the source metadata. They may need
  compilers, CMake, Ninja, Python headers, a matching PyTorch build, and a
  CUDA toolkit. Do not promise a wheel or build duration.
- AIFS and its ensemble variants depend on `flash-attn`; Atlas and some
  StormCast variants depend on `natten`; FCN3, SFNO, and perturbation depend on
  `torch-harmonics`.
- GraphCast and GenCast use WeatherNext and require Python 3.12 or newer in
  their extras. Their extra also selects JAX with CUDA-13 support, Haiku,
  Flax, and related dependencies.
- FengWu, FuXi, and Pangu use `onnx`, `onnxscript`, and
  `onnxruntime-gpu>=1.21.0` in this snapshot. ONNX Runtime's CUDA provider must
  match the installed CUDA/PyTorch environment; an installed import alone is
  not proof that GPU binding works.
- `da-healda`, `da-interp`, and `da-stormcast` select `cupy-cuda13x` and
  `cudf-cu13`; `da-cosmo` selects CUDA-13 CuPy and the COSMO dependency chain.
  These extras are not CPU-neutral.
- The broad `all` extra is intentionally composed of broad groups and selected
  model families. It is resource-heavy and does not supersede the explicit uv
  conflicts. Prefer targeted environments for reproducible work.

## Build and system preparation

If the user selects a source-built extra, surface these prerequisites before
installation:

- A `Python.h` error means Python development headers are missing. Install the
  operating-system equivalent of Python development tools, then retry the
  user-run package command.
- A missing CMake executable means CMake is not on `PATH` for a build such as
  `dm-tree` or `natten`.
- Flash Attention can build for a long time. A compatible prebuilt wheel or an
  NVIDIA PyTorch container may be preferable; increasing `MAX_JOBS` trades
  memory for compile time.
- FCN3/SFNO CUDA extension builds may use `FORCE_CUDA_EXTENSION=1` and a
  task-specific `TORCH_CUDA_ARCH_LIST`, but only after confirming the GPU
  architecture and the selected package's build instructions.
- Do not use `--no-build-isolation` indiscriminately. Apply it only where the
  selected extra's metadata or install guidance requires it, with PyTorch
  already available.

The install command is not a checkpoint download. Model assets may be fetched
later by an AutoModel load, and data connectors may access remote stores later.

## Cache, access, and license boundaries

The package defaults to `~/.cache/earth2studio` for cache material. The following
environment variables can override behavior:

| Variable | Effect |
| --- | --- |
| `EARTH2STUDIO_CACHE` | General model/data cache root. |
| `EARTH2STUDIO_DATA_CACHE` | Data-source cache; overrides the general root for data. |
| `EARTH2STUDIO_MODEL_CACHE` | Model package/checkpoint cache; overrides the general root for model assets. |
| `EARTH2STUDIO_PACKAGE_TIMEOUT` | Timeout in seconds for model package access; invalid values fall back to the default. |

Set cache paths only after checking disk quotas and shared-filesystem policy.
Remote data-source caching and model-package caching are separate budgets even
when they share a root. A cache path does not grant access, and deleting or
relocating it is a user-controlled operation outside this sub-skill.

Earth2Studio is Apache-2.0, but model checkpoints, third-party code, and data
providers have their own terms. Before recommending a candidate, record the
provider, whether access is public or credentialed, whether redistribution is
allowed, and whether the user has accepted the relevant terms.

## AutoModel access pattern

The stable interface for a supported pre-trained class is:

```python
from earth2studio.models.auto import Package

package = SomeModel.load_default_package()
model = SomeModel.load_model(package)
```

`load_default_package()` creates a `Package` reference; it does not itself
perform the asset download. `load_model(package)` can resolve files and trigger
access. For a user-owned package, the mixin also supports:

```python
model = SomeModel.from_pretrained("/path/to/package")
model = SomeModel.from_pretrained("hf://...")
model = SomeModel.from_pretrained("s3://...")
model = SomeModel.from_pretrained("ngc://models/...@...")
```

The URI is an access and licensing decision, not a discovery proof. Keep
credentials out of prompts and logs. If a public NGC asset is rejected because
of stale NGC configuration, inspect the user's NGC environment/configuration
and provider policy rather than embedding credentials in a workflow.
