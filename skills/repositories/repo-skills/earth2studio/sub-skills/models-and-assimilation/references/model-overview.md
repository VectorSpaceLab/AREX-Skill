# Model-family routing

This reference is a bounded route map for the public Earth2Studio model exports.
It is intentionally representative, not an exhaustive inventory or a promise that
every checkpoint is available for every version, device, or region.

## Choose by behavior

| Need | Start with | Contract to inspect |
|---|---|---|
| Global time integration | px classes such as `FCN`, `SFNO`, `Pangu3/6/24`, `FuXi`, `AIFS`, `Aurora`, `GraphCastOperational`, `GenCastMini`, `Atlas`, `ACE2ERA5`, `DLWP`, or `DLESyM` | Tensor plus ordered `CoordSystem`; model-native `lead_time` |
| Global ensemble | `AIFSENS`, `AIFS2ENS`, `Aurora1p5Ensemble`, or another class explicitly exposing ensemble behavior | Batch/ensemble dimensions, stochastic seed, memory, and output coordinates |
| Regional forecast / convection nowcast | `StormCast`, `StormCastCONUS` | HRRR-shaped regional grid, conditioning source, hourly step, and optional observations for supported variants |
| Satellite/radar nowcast | `StormScopeGOES`, `StormScopeMRMS` | History window, model variant (`3km_10min` or `6km_1hr`), input interpolation, and GOES/MRMS/GLM coupling |
| Generative downscaling | `CorrDiff`, `CorrDiffTaiwan`, `CorrDiffCMIP6`, `CorrDiffCosmoEra5`, `CBottleSR`, or `CBottleInfill` | Diagnostic input grid/variables, output `sample` dimension, resolution/mode, and spatial domain |
| Physical/derived diagnostic | `Identity`, `DerivedWS`, `DerivedRH`, `DerivedVPD`, `DerivedSurfacePressure`, `DerivedTCWV`, or an AFNO precipitation/solar/wind-gust class | Required input variables and exact output variable/unit transform |
| Tropical-cyclone or event product | `TCTrackerWuDuan`, `TCTrackerVitart`, `StormScopeDxNSRDB`, or a product-specific class | Product-specific fields, region, and optional backend; do not treat it as a generic field transform |
| Seasonal/coupled atmosphere-ocean | `DLESyM`, `DLESyMLatLon`, `DLESyMv0_ISCCP_ERA5`, or its lat/lon variant | HEALPix versus lat/lon, derived variables, atmosphere/ocean cadence, and valid-output helpers |
| Observation interpolation | `InterpEquirectangular` | Observation `FrameSchema`, time tolerance, interpolation method, and xarray output |
| Global analysis from sparse observations | `HealDA` | Conventional/satellite schemas, request-time metadata, HEALPix or optional lat/lon output |
| Regional score-based DA | `StormCastSDA` or `CorrDiffCosmoEra5SDA` | Background-state schema, observation operator, conditioning source, and generator semantics |

## Prognostic families

A prognostic model is a state transition. Its protocol is structural: it need
not inherit `PrognosticModel`. Use:

```python
x1, c1 = model(x0, c0)                 # one native transition
iterator = model.create_iterator(x0, c0)  # initial state is normally first
x_step, c_step = next(iterator)
```

`input_coords()` and `output_coords()` may reveal different lead-time spacing,
required history, pressure-level variables, or spatial axes. Models with a
`PrognosticMixin` may expose iterator hooks, but those hooks are not a substitute
for the public protocol.

### Downscaling and nowcasting distinctions

- `CorrDiff*` classes are diagnostics: they do not advance the atmospheric
  state. Diffusion variants can produce multiple samples and should be treated
  as an instantaneous conditional distribution.
- `StormCast` is a regional generative prognostic and can use a global
  conditioning data source. `StormCastCONUS` has additional SDA-related model
  parameters and a generator that can receive observations.
- `StormScopeGOES` is a GOES-channel prognostic. `StormScopeMRMS` forecasts
  radar/GLM fields and can be conditioned on GOES. The coupled path has a
  `call_with_conditioning` seam; do not call the MRMS model as if it were a
  generic standalone tensor model without checking its configured sources.
- `CBottleVideo` and `UCast` are additional video/nowcast-style exports; their
  history and backend requirements must be read from their own coordinate
  methods before use.

## DLESyM and seasonal routing

DLESyM is a coupled Earth-system prognostic rather than a conventional single-
field weather rollout. `DLESyM` works in its native HEALPix representation;
`DLESyMLatLon` performs the lat/lon convenience conversion so ordinary lat/lon
inputs can be used. The ISCCP-ERA5 variants include the `ttr`/OLR conversion
and pair with `DLESyMv0_ISCCP_ERA5Precip` for precipitation diagnostics.

One coupled step can emit multiple atmosphere and ocean lead times. Use the
model's `retrieve_valid_atmos_outputs` and `retrieve_valid_ocean_outputs` helpers
rather than assuming every ocean field exists at every atmosphere lead time.
When chaining the ISCCP precipitation diagnostic, reorder the variable axis to
`precip.input_coords()["variable"]` and use the required two-frame history.

Seasonal statistics and IO are downstream consumers, not model families. Keep
this skill focused on selecting a prognostic and preserving its valid lead-time
contract; use the run/statistics skill for aggregation and persistence.

## Package and capability boundaries

Model names do not imply that weights are installed. A class can import while
its constructor is guarded by an optional-dependency check, and `load_model` can
fail later when a compiled backend or a checkpoint asset is missing. Check the
narrow extra and device before loading. Representative extra mappings are in
[API reference](api-reference.md); predictable failures and recoveries are in
[troubleshooting](troubleshooting.md).
