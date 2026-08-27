# Model and loader API reference

The source package version covered by this skill is `0.18.0a0`, with Python
`>=3.11,<3.15`. Signatures below are the verified public signatures that matter
for routing; model constructors and checkpoint contents can change between
releases.

## Structural protocols

```python
# PrognosticModel
model(x: torch.Tensor, coords: CoordSystem) -> tuple[torch.Tensor, CoordSystem]
model.create_iterator(x, coords) -> Iterator[tuple[torch.Tensor, CoordSystem]]
model.input_coords() -> CoordSystem
model.output_coords(input_coords) -> CoordSystem
model.to(device) -> PrognosticModel

# DiagnosticModel
model(x: torch.Tensor, coords: CoordSystem) -> tuple[torch.Tensor, CoordSystem]
model.input_coords() -> CoordSystem
model.output_coords(input_coords) -> CoordSystem
model.to(device) -> DiagnosticModel

# AssimilationModel
model(*args) -> tuple[pd.DataFrame | xr.DataArray, ...]
model.create_generator(*args) -> Generator[tuple[...], tuple[..., ...], None]
model.init_coords() -> tuple[FrameSchema | CoordSystem, ...] | None
model.input_coords() -> tuple[FrameSchema | CoordSystem, ...]
model.output_coords(input_coords, *args, **kwargs) -> tuple[FrameSchema | CoordSystem, ...]
model.to(device) -> AssimilationModel
```

These are protocols, not required base classes. A concrete model may return an
xarray `DataArray` directly, especially the current DA implementations. Always
inspect the concrete class and its coordinate methods.

## Auto loading and package access

```python
from earth2studio.models.auto import AutoModelMixin, Package

Package(root, fs=None, fs_options={}, cache=None, cache_options={})
AutoModelMixin.from_pretrained(pretrained_model_name_or_path=None)
Class.load_default_package()
Class.load_model(package, ...)
```

`Package` abstracts a local or fsspec-backed root. The implemented remote root
families include `hf://`, `s3://`, and `ngc://models/...`; local paths are also
valid. `resolve(file_path)` fetches/caches and returns a local path,
`open(file_path)` returns a buffered reader, and `get(file_path)` is a deprecated
compatibility alias for `resolve`. A default cache is under the user's
Earth2Studio cache location and can be changed with `EARTH2STUDIO_CACHE` or
`EARTH2STUDIO_MODEL_CACHE`; `EARTH2STUDIO_PACKAGE_TIMEOUT` controls the package
request timeout. Do not put credentials or tokens in a skill or command.

`load_default_package()` creates a package object and generally does not fetch
an asset. `load_model()` commonly calls `package.resolve()` and can download
large weights. Keep that action explicit and run it only after the extra,
backend, storage, and device gates pass.

## Representative exact loaders

```python
from earth2studio.models.px import FCN, StormCast, DLESyM, DLESyMLatLon
from earth2studio.models.dx import CorrDiffTaiwan, CorrDiffCosmoEra5
from earth2studio.models.da import (
    InterpEquirectangular, HealDA, StormCastSDA, CorrDiffCosmoEra5SDA,
)

FCN.load_model(package)
StormCast.load_model(package, conditioning_data_source=..., sampler_steps=18)
DLESyM.load_model(package, atmos_model_idx=0, ocean_model_idx=0)
DLESyMLatLon.load_model(package, atmos_model_idx=0, ocean_model_idx=0)
CorrDiffTaiwan.load_model(package, device=None)
CorrDiffCosmoEra5.load_model(
    package, device=None, mode="mean", resolution="rea6",
    hub_heights=None, hub_interp="linear",
)
InterpEquirectangular(
    lat=None, lon=None, interp_method="smolyak",
    time_tolerance=np.timedelta64(10, "m"),
)
HealDA.load_model(
    package, lat_lon=False, output_resolution=(181, 360),
    time_tolerance=(np.timedelta64(-21, "h"), np.timedelta64(3, "h")),
)
StormCastSDA.load_model(
    package, conditioning_data_source=..., time_tolerance=np.timedelta64(10, "m"),
    sampler_steps=36, sda_std_obs=0.1, sda_gamma=0.001,
)
CorrDiffCosmoEra5SDA.load_model(
    package, assimilate_variables=("u10m", "v10m"), resolution="rea2",
    domain=None, time_tolerance=np.timedelta64(10, "m"),
    number_of_samples=None, sampler_steps=None, sda_std_obs=0.5,
    sda_gamma=5e-5, amp=False,
)
```

The `...` conditioning source above is intentional: it is a required model-
specific dependency for some models and is not a data-source catalog. Resolve
it from the model configuration and its `input_coords`, not from this snippet.

## Optional extra routing

Install only the selected group, for example `uv sync --extra corrdiff` or
`uv sync --extra da-healda`. Groups below are the relevant public package
names; each group may also have platform/version markers.

### Prognostic groups

| Family / export examples | Extra |
|---|---|
| `ACE2ERA5` | `ace2` |
| `AIFS`, `AIFSENS` | `aifs` or `aifsens` |
| `AIFS2`, `AIFS2ENS` | `aifs2` or `aifs2ens` |
| `Atlas` | `atlas` |
| `Aurora` | `aurora` |
| `DLESyM` variants | `dlesym` |
| `DLWP` | `dlwp` |
| `FCN` | `fcn` |
| `FCN3` | `fcn3` |
| `FengWu`, `FuXi` | `fengwu` or `fuxi` |
| `GenCastMini` | `gencast` |
| `GraphCastOperational`, `GraphCastSmall` | `graphcast` |
| `InterpModAFNO` | `interp-modafno` |
| `Pangu3`, `Pangu6`, `Pangu24` | `pangu` |
| `SFNO` | `sfno` |
| `StormCast` | `stormcast` |
| `StormCastCONUS` | `stormcast-conus` |
| `StormScopeGOES`, `StormScopeMRMS` | `stormscope` |
| `CBottleVideo` | `cbottle` |
| `UCast` | no model-specific packages in the declared group |

### Diagnostic groups

| Family / export examples | Extra |
|---|---|
| `CBottleInfill`, `CBottleSR`, `CBottleTCGuidance` | `cbottle` |
| `ClimateNet` | no model-specific packages in the declared group |
| `CorrDiff`, `CorrDiffTaiwan` | `corrdiff` |
| `CorrDiffCMIP6`, `CorrDiffCosmoEra5` | `cosmo` for COSMO; `corrdiff` for the base family |
| derived diagnostics and `Identity` | no model-specific packages in the declared group |
| `OrbitGlobalPrecip` | `orbit` |
| `PrecipitationAFNO` | `precip-afno` |
| `PrecipitationAFNOv2` | `precip-afno-v2` |
| `SolarRadiationAFNO1H/6H` | `solarradiation-afno` |
| `WindgustAFNO` | `windgust-afno` |
| `StormScopeDxNSRDB` | `stormscope` |
| cyclone tracking classes | `cyclone` |

### Assimilation groups

| Class | Extra |
|---|---|
| `InterpEquirectangular` | `da-interp` |
| `HealDA` | `da-healda` |
| `StormCastSDA` | `da-stormcast` |
| `CorrDiffCosmoEra5SDA` | `da-cosmo` |

These are dependency groups, not capability guarantees. Several include CUDA
libraries or compiled extensions (`cupy`, `cudf`, NATTEN, torch-harmonics,
PhysicsNeMo, ONNX Runtime GPU, or Flash Attention). A CPU-only host may be able
to inspect a class but still cannot execute a GPU-only configuration.

## Device and validation commands

Use the repository's supported runner and inspect before a real load:

```bash
uv run python -c 'import torch; print(torch.__version__); print(torch.cuda.is_available())'
uv run python -c 'from earth2studio.models.px import FCN; print(FCN.load_default_package())'
uv run python path/to/earth2studio-skill/sub-skills/models-and-assimilation/scripts/check_model_contract.py --tiny-fixture
```

The second command only prints a package pointer for a normal auto model; do
not assume that the subsequent `load_model` is offline.
