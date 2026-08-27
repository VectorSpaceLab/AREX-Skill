# Model, data, lexicon, and backend overview

Use this reference to turn a task description into a small candidate set. Names
below are observed public package exports in the `0.18.0a0` source snapshot and
are examples for triage, not an exhaustive support list. Always confirm the
installed version's API and the selected extra before recommending a class.

## Task-to-family triage

| User asks for | Start with | Questions that change the result |
| --- | --- | --- |
| A state advanced through forecast lead times | Prognostic/PX model | Global versus regional domain, nowcast versus medium-range/seasonal horizon, deterministic versus ensemble, VRAM, and input cadence. |
| Downscaling, derived fields, precipitation, radiation, wind gust, or cyclone tracking | Diagnostic/DX model | Required input/output variables, source grid, regional coverage, and whether an external tool or model checkpoint is needed. |
| Assimilation of observations into a model state | DA model | Observation type, spatial/temporal alignment, CUDA CuPy/cuDF support, and beta API stability. |
| Data inspection or preparation | Data/forecast/dataframe source | Analysis versus forecast, array versus tabular return type, time/lead-time coverage, credentials, and cache policy. |
| Output persistence or storage comparison | IO backend | Local file, cloud/object store, memory/key-value store, asynchronous writes, datetime handling, and filesystem inode budget. |

Do not select a model before the user supplies at least the task family,
region/temporal scale, variables or product, and hardware/access constraints.

## Representative model routes

### Prognostic (PX)

The package exports representative forecast classes including `AIFS`, `AIFS2`,
`AIFSENS`, `AIFS2ENS`, `Aurora`, `Aurora1p5`, `Aurora1p5Ensemble`, `FCN`, `FCN3`,
`GraphCastOperational`, `GraphCastSmall`, `GenCastMini`, `FengWu`, `FuXi`,
`Pangu3`, `Pangu6`, `Pangu24`, `SFNO`, `StormCast`, `StormCastCONUS`, `Atlas`,
`DLESyM`, `DLWP`, and `UCast`. The export surface also contains specialized or
wrapper classes. Use the model's API page or installed class to determine
release, domain, cadence, expected variables, and checkpoint source.

Useful first-pass routes:

- Medium-range/global forecast: compare a small number of global PX candidates
  such as AIFS, Aurora, FCN/FCN3, or GraphCast, then verify data lexicons and
  checkpoint access.
- Regional/convective nowcasting: investigate StormCast, StormCastCONUS, or
  StormScope routes, with explicit regional and extra/build checks.
- Seasonal/climate or statistical use: investigate DLESyM and the relevant
  statistics/data routes; do not assume medium-range input conventions apply.
- Ensemble uncertainty: choose an ensemble-capable model family and separate
  ensemble/perturbation dependencies from the deterministic base model.

### Diagnostic (DX)

Representative exports include `CorrDiff`, `CorrDiffCMIP6`,
`CorrDiffCosmoEra5`, `CorrDiffTaiwan`, `ClimateNet`, `CBottleInfill`,
`CBottleSR`, `CBottleTCGuidance`, `PrecipitationAFNO`,
`PrecipitationAFNOv2`, `SolarRadiationAFNO1H`, `SolarRadiationAFNO6H`,
`WindgustAFNO`, `OrbitGlobalPrecip`, `StormScopeDxNSRDB`, and tropical-cyclone
tracker classes. Treat `precip-afno-v2` as a compatibility choice requiring
review because the install selector marks it as deprecated and lower-performing
than v1. Cyclone tracker workflows can require the separately installed
TempestExtremes tool; the Python extra alone is not sufficient.

### Data assimilation (DA)

The package exports `HealDA`, `InterpEquirectangular`, `StormCastSDA`, and
`CorrDiffCosmoEra5SDA` in this snapshot. DA APIs are beta. The DA extras are
CUDA-oriented: check CuPy/cuDF and PhysicsNeMo/COSMO dependencies before
shortlisting them. Observation sources and model input coordinates must be
aligned; an observation variable name matching the lexicon does not guarantee
that its time, footprint, or quality-control semantics fit the model.

## Data-source routes

Built-in exports include analysis/reanalysis and forecast sources such as
`GFS`, `GFS_FX`, `HRRR`, `HRRR_FX`, `ARCO`, `CDS`, `IFS`, `IFS_FX`, `GEFS_FX`,
`CFS_FX`, `DynamicalGFS`, `DynamicalHRRR`, `DynamicalGEFS`, `DynamicalAIFS`,
`EarthMoverERA5`, `WB2ERA5`, and local xarray/file sources. Observation and
satellite-oriented examples include `GHCNHourly`, `ISD`, `GOES`, `GOESGLMGrid`,
`MRMS`, `JPSS`, `HimawariAHI`, `MetOp*`, `MeteosatFCI`, `OPERA`, `UFSObsConv`,
and `UFSObsSat`. These are routing examples, not a promise that every source
has the variables, dates, region, or credentials a user needs.

Use the interface shape to classify a source:

| Source interface | Input shape | Return shape |
| --- | --- | --- |
| `DataSource` | `(time, variable)` | xarray `DataArray` |
| `ForecastSource` | `(time, lead_time, variable)` | xarray `DataArray` |
| `DataFrameSource` | `(time, variable)` | pandas `DataFrame` |
| `ForecastFrameSource` | `(time, lead_time, variable)` | pandas `DataFrame` |

`earth2studio.data.fetch_data(...)` and `fetch_dataframe(...)` are workflow
utilities whose signatures are useful for planning device and return-type
requirements, but this sub-skill does not call them. Discovery should not use a
remote source's `available()` or `__call__` method as a disguised data fetch.
Ask the user to run such a check only in a later, explicitly approved data
workflow.

## Lexicon compatibility gate

Earth2Studio variable identifiers are short, explicit keys. Examples include
`t2m`, `u10m`, `v10m`, `u200`, `z500`, `tcwv`, `sp`, `tp`, `lat`, and `lon`.
Pressure-level names have no suffix (`z500` means a pressure level); height
above the surface uses an `m` suffix (`u10m`); source-specific/custom vertical
levels need caution because equal-looking indices may not be interoperable.

Use this gate before recommending a source/model pair:

1. Inspect the model's `input_coords()` and isolate its `variable` coordinate,
   including all requested pressure or height levels and metadata fields.
2. Inspect the candidate source lexicon class's `VOCAB` keys. A source key is
   an Earth2Studio identifier mapped to a provider-native field; it is not
   necessarily the provider's complete inventory.
3. Compute the missing set: `required_variables - set(source_lexicon.VOCAB)`.
   An empty set is necessary for the variable-name layer only.
4. Continue with grid/coordinate order, resolution, domain, lead-time cadence,
   historical/operational date range, and provider availability. Check source
   documentation for modifiers and units; the same identifier from two sources
   may not be numerically identical.
5. If a variable is missing, switch source, choose a model with a smaller input
   contract, or explicitly plan a conversion/custom source. Do not silently
   rename a missing field.

Useful source lexicon families visible in the package include GFS, HRRR, CDS,
ARCO, ECMWF/IFS/AIFS, GEFS, CFS, WB2, Dynamical, EarthMover, GOES, MRMS,
JPSS, and observation lexicons. The lexicon is the source of truth for the
Earth2Studio spelling and provider translation; it does not prove remote access.

## Examples as workflow patterns

Recommend only one to three patterns after task triage:

- `01_getting_started`: deterministic, diagnostic, ensemble, and checkpoint
  restart patterns.
- `02_medium_range`: extending ensembles, perturbation hooks, large ensembles,
  temporal interpolation, cyclone tracking, and Atlas.
- `03_downscaling`: CorrDiff, CBottle super-resolution, ensemble downscaling,
  and COSMO reanalysis downscaling.
- `04_nowcasting`: StormCast deterministic/ensemble and StormScope satellite
  routes.
- `05_data_assimilation`: StormCast SDA, HealDA, and CorrDiff COSMO SDA.
- `06_seasonal`: seasonal statistics and DLESyM climate routes.
- `07_misc`: distributed management, generation, IO performance, and local
  data-source patterns.
- `08_extend`: custom prognostic, diagnostic, and data-source interfaces.

Treat an example as a pattern to inspect later, not as an instruction to run
it now. The example's model extra, checkpoint access, source dates, credentials,
and hardware may differ from the user's environment.

## Output backend fit

All listed backends are exported from `earth2studio.io` in the verified source.
Use the following discovery screen:

| Backend | Fit signal | Explicit limit |
| --- | --- | --- |
| `ZarrBackend` | Default persistent array store; datetime-friendly and common in examples. | Still needs a later workflow to initialize/write arrays. |
| `AsyncZarrBackend` | Non-blocking/sharded writes for large forecast campaigns. | Many small chunks can exhaust inode quotas; shard design and memory need review. |
| `NetCDF4Backend` | NetCDF-compatible file output, used by seasonal/statistics patterns. | NetCDF4/system dependency and format constraints apply. |
| `XarrayBackend` | In-memory or xarray-oriented output handling. | Storage behavior follows xarray kwargs and is not a remote-data selector. |
| `KVBackend` | Key/value or device-oriented in-memory use cases. | Not a general replacement for a durable file/object store. |

This table selects a storage direction only. It does not authorize inference,
remote writes, cloud credentials, or serving.

## Discovery response shape

Return a compact record with:

- task family, region, horizon, variables/levels, ensemble mode, and hardware;
- candidate class and extra, with why it fits and what remains unverified;
- candidate source and lexicon class, required/missing variables, grid/time/access
  notes, and whether it returns arrays or dataframes;
- one to three example patterns and a backend recommendation;
- checkpoint/data provider, license/access/cache notes;
- exact read-only imports or metadata checks for the user to run next.
