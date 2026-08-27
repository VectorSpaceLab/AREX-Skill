# Data-assimilation contracts

Data assimilation (DA) combines observations with a model state or background.
The public protocol is structural and accepts a tuple of tabular or xarray
inputs, but current concrete classes have intentionally different call and
generator shapes. Inspect `init_coords()`, `input_coords()`, and
`output_coords(...)` on the selected class before constructing data.

## Stateless versus stateful

### Stateless call

Use a direct call when each request is independent:

```python
analysis = model(observations)
# or, for two HealDA streams:
analysis = model(conv_obs=conv_df, sat_obs=sat_df)
# or for a background-state DA model:
analysis = model(background_xarray, obs_df)
```

Do not assume all results are tuples. Interpolation, HealDA, StormCast SDA,
and CorrDiff COSMO SDA return xarray `DataArray` objects in their concrete
implementations. Check `analysis.dims`, `analysis.coords`, and the data device.

### Stateful generator

A generator preserves or advances state between observation batches, but its
priming convention is concrete-model-specific:

| Model | Create | Prime | Send | Meaning |
|---|---|---|---|---|
| `InterpEquirectangular` | `g = model.create_generator()` | `g.send(None)` yields `None` | `g.send(obs_df)` | independent interpolation steps |
| `HealDA` | `g = model.create_generator()` | `g.send(None)` yields `None` | `g.send((conv_df, sat_df))` | repeated global analyses; either frame may be `None`, not both |
| `StormCastSDA` | `g = model.create_generator(x0)` | `next(g)` yields initial state | `g.send(obs_df_or_None)` | advances the HRRR state by one hour; `None` means no observations |
| `CorrDiffCosmoEra5SDA` | `g = model.create_generator(x)` | `next(g)` yields `None` | `g.send(obs_df_or_None)` | independent analysis for each input time; not a propagated forecast |

Close generators in a `finally` block. For a finite sequence, stop when the
concrete generator raises `StopIteration`; do not blindly send after the
model's available input times are exhausted.

## Observation frame schema

The common sparse observation fields are:

```text
time, lat, lon, observation, variable
```

They are not interchangeable with arbitrary DataFrame columns. The selected
model can require additional fields, and `FrameSchema` may constrain dtypes or
allowed variable values. Validate required fields before time filtering. Use
`earth2studio.models.da.utils.validate_observation_fields` when using the
package helper; it raises `ValueError` listing missing and available fields.

`filter_time_range` applies the model's `time_tolerance`. A scalar tolerance is
symmetric; a pair is `(lower, upper)`. A source DataFrame may need
`attrs["request_time"]` so the model can produce the requested output time.
Keep observation units in the convention expected by the model; for example,
HealDA converts conventional pressure-like fields from Pa to hPa internally,
while other models map physical observations through their own output scale.
Do not perform a second conversion without checking the class.

## InterpEquirectangular

This lightweight DA model accepts one DataFrame with the fields above plus
`variable` values from `t2m`, `u10m`, `v10m`, and `sp`. Its constructor is:

```python
InterpEquirectangular(
    lat=None,
    lon=None,
    interp_method="smolyak",  # also "nearest"
    time_tolerance=np.timedelta64(10, "m"),
)
```

`input_coords()` returns one `FrameSchema`; `output_coords(...,
request_time=...)` returns a tensor-style coordinate system with dimensions
`time, variable, lat, lon`; `__call__(obs)` returns an xarray DataArray. The
`request_time` metadata is required by the concrete `__call__` path. Missing a
variable at a requested time leaves NaNs for that variable/time; an invalid
interpolation method fails at construction.

The model can use CuPy on CUDA. On a CPU, use the default CPU path and do not
assume cudf is installed. Its `dfseries_to_torch` helper uses zero-copy dlpack
for cudf where available and warns when pandas values are copied to a GPU.

## HealDA

`HealDA` is a stateless global analysis model. Its two input schemas are:

- conventional: `time`, `lat`, `lon`, `observation`, `variable`, `type`,
  `elev`, `pres`; variables include `u`, `v`, `q`, `t`, `pres`, `gps`,
  `gps_t`, and `gps_q`;
- satellite: `time`, `lat`, `lon`, `observation`, `variable`,
  `sensor_index`, `satellite`, `scan_angle`, `satellite_za`, `solza`; variables
  include `atms`, `mhs`, `amsua`, and `amsub`.

At least one of `conv_obs` or `sat_obs` must be non-`None`; each present frame
must carry `attrs["request_time"]`. `model(conv_obs=..., sat_obs=...)` returns
an analysis with `time` and `variable` plus either native `npix` or, when
loaded with `lat_lon=True`, regular `lat` and `lon` dimensions. The standard
Earth2Studio variable names include `t2m`, `u10m`, `v10m`, `msl`, and pressure
levels, but query the actual output coordinates rather than hard-coding a
complete channel list.

`HealDA.load_model(package, lat_lon=False, output_resolution=(181, 360),
time_tolerance=...)` loads its weights and normalization assets. The optional
lat/lon conversion does not make the underlying HEALPix model a generic regular
grid model; preserve the output coordinates returned by the instance.

## StormCastSDA

`StormCastSDA` assimilates sparse observations into a one-hour HRRR regional
forecast. It requires a background `x` on the model's HRRR curvilinear grid and
an observation frame with `time`, `lat`, `lon`, `observation`, and `variable`.
`init_coords()` describes the state with `time`, `lead_time=[0 h]`, `variable`,
`hrrr_y`, and `hrrr_x`; `input_coords()` describes the observation frame.
`output_coords` advances `lead_time` by one hour and validates the HRRR spatial
sizes and variable coordinate.

The generator's first yielded value is the initial state. Each `send(obs)`
advances one hour; send `None` when no observations are available. The model
also needs a `conditioning_data_source`; if it is absent, construction warns
and execution raises a conditioning-source error. Observation points outside
the regional polygon or outside the time tolerance are ignored. Use a small
regional crop and reduced sampler settings only when the model's loader exposes
those parameters; do not invent a generic `batch_size` or resolution flag.

## CorrDiffCosmoEra5SDA

This class wraps a diffusion-mode `CorrDiffCosmoEra5` diagnostic downscaler. It
is a single-shot analysis, not a propagated state. The background input is an
xarray DataArray with `time`, `variable`, `lat`, and `lon`; a size-one
`lead_time` is accepted and squeezed. Observation frames use the common five
fields. The output has dimensions `time, sample, variable, y, x` and 2-D `lat`
and `lon` coordinates.

Required configuration includes `assimilate_variables`. They must be output
channels with identity transform and unit scale. Representative valid choices
are `("u10m", "v10m")` or terrain-following `("u3d_l47", "v3d_l47")` when
those channels exist in the selected resolution. A `sda_std_obs` mapping must
contain exactly the assimilated variables; every value must be finite and
positive. `sda_gamma` must be finite and non-negative. `domain` is forwarded to
the wrapped downscaler before the SDA wrapper is built, so do not crop the
wrapped model afterward.

With the generator, `next(g)` yields `None`; each `send(obs_or_None)` produces
one independent analysis for the next input time. This is different from
StormCastSDA even though both use diffusion posterior sampling.

## Synthetic stateful case

For a hard schema check without weights, model the StormCastSDA pattern:

1. Define `x0` with dimensions `(time, lead_time, variable, hrrr_y, hrrr_x)`,
   `lead_time=[0 h]`, and a variable list matching `model.init_coords()`.
2. Define `obs` with exactly the fields returned by `model.input_coords()` and
   finite `time`, `lat`, `lon`, `observation`, and allowed `variable` values.
3. Prime with `state = next(generator)` and assert its coordinates equal `x0`.
4. Send `obs`; assert the result retains `time`, `variable`, `hrrr_y`, and
   `hrrr_x`, and that `lead_time` advanced by one hour.
5. Send `None`; assert another one-hour transition, then close the generator.

The bundled checker exercises this pattern with a tiny standard-library fake;
it proves generator/schema mechanics, not model quality or checkpoint validity.
