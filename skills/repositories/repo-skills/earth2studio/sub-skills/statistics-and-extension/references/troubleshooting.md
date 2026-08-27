# Troubleshooting and recovery

Use the first observable failure to choose a repair. Do not mask a coordinate or
optional-dependency error with a reshape, `squeeze`, or broad exception handler.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `KeyError` for a reduction or required axis | The coordinate mapping does not contain the declared dimension | Print `list(coords)`, add the dimension at the real tensor axis, or change the declared reduction contract. Do not infer an axis from tensor rank. |
| Output tensor and mapping have different lengths | `output_coords` removed/added the wrong axis or the numerical method changed shape | Assert `list(out.shape) == [len(v) for v in out_coords.values()]`; update both together. |
| Diagnostic output has no `variable` coordinate | A derived field was computed but not advertised | Return a variable array with one entry per output field and validate it before the forward operation. |
| Same-shaped metric returns suspicious values | Forecast and truth mappings are reordered or labels differ | Compare ordered axis names and coordinate values; reject the call before subtraction. Then map/reorder explicitly and rerun the tiny case. |
| Metric says truth contains `ensemble` | CRPS, rank, energy score, or an ensemble metric was given an ensemble truth | Remove the ensemble from truth and use matching non-ensemble axes. If truth is itself an ensemble, define a separate reduction contract rather than relying on broadcasting. |
| `ValueError` about weights dimensions/shape | `weights.ndim` does not equal the number of reduction axes, or lengths/order differ | Build weights as `[len(coords[d]) for d in coords if d in reduction_dimensions]`; include every reduced axis in coordinate order. |
| Weighted result differs from reference | Latitude orientation, units, device, or normalization is inconsistent | Use degree coordinates and `lat_weight`; compare a two-cell hand calculation; move weights to the tensor device; confirm the source values are physical units. |
| Batch-updated result leaks between runs | A stateful statistic was reused for independent streams | Construct a fresh object per forecast/experiment or reset its state deliberately. Test split-vs-single-call equivalence. |
| `handshake_dim` rejects a custom model | The ordered mapping does not match the tensor layout | Fix `input_coords`, tensor permutation, or both. Keep public latitude north-to-south and longitude `0..360` unless the component explicitly documents another internal layout. |
| `batch_func` reports invalid positional arguments | A decorated method received keyword tensor/coordinate inputs or an unpaired argument | Call with `(x, coords)` pairs; use keyword arguments only for non-batched configuration. Ensure all paired inputs have the same outer batch shape. |
| Prognostic iterator starts at lead time one | The generator yielded only the result of `__call__` | Yield `(x, coords)` unchanged before the first model step, then advance `lead_time` per step. |
| Diagnostic workflow cannot map prognostic output | Diagnostic input axes/variables do not match the prognostic output | Use `map_coords` for a supported subset or make the diagnostic input contract match. Do not drop `lead_time` accidentally in a prognostic path. |
| Source returns wrong tensor order | xarray dimensions/coordinates do not match the source protocol expected by `fetch_data` | Inspect `DataArray.dims`, `DataArray.sizes`, and coordinate values in a local fixture; return explicit time/lead-time/variable axes and test `fetch_data`. |
| `fetch_dataframe` output lacks request metadata | The helper was bypassed or attrs were discarded | Route DA observation requests through `fetch_dataframe`, preserve `attrs["request_time"]` and `attrs["request_lead_time"]`, and validate them at model entry. |
| DataFrame `fields` fails | Field is not in `SCHEMA` or has an incompatible type | Resolve/validate fields against the declared PyArrow schema; use `E2STUDIO_SCHEMA` names where possible. |
| Observation window is unexpectedly empty | Symmetric/asymmetric tolerance was interpreted manually or in the wrong sign | Type the parameter as `TimeTolerance`, call `normalize_time_tolerance` once, check lower <= upper, and pass normalized bounds to the filtering helper. |
| Custom variable cannot be fetched | It is absent from the data-source lexicon or model vocabulary | Add an explicit tested lexicon mapping/modifier, or request only supported variables. Do not claim that a remote variable is universally portable. |
| Optional dependency error names `statistics` | CRPS/rank/fair scoring or another optional implementation needs the statistics extra | Install the documented optional group in the consumer environment, or test a core moment/RMSE path without that feature. Do not import a heavy backend in the smoke script. |
| Optional dependency error names `perturbation` | Spherical/Gaussian correlated perturbation needs the perturbation extra | Install that targeted extra and verify its compatible Torch/CUDA build; use `Zero` or a tiny Torch-only perturbation for offline tests. |
| CUDA DataFrame conversion fails | cudf/cupy is absent or incompatible | Run the pandas/CPU contract first; classify CUDA tabular support as unavailable until the matching optional packages are installed. |
| Torch extension has an undefined symbol | A compiled package was built against another Torch/CUDA version | Rebuild/reinstall the affected targeted extra in a clean compatible environment; do not change component code to suppress the import. |
| Remote data/model test hangs or is unauthorized | Network, credentials, or checkpoint access is required | Stop the remote check, preserve the exact command/error, and use a local synthetic fixture as the strict gate. Never add credentials or downloads to `contract_smoke.py`. |
| IO write fails after a valid component call | The IO coordinate mapping does not match the output tensor or backend requirements | Validate the output mapping before `io.write`; start with `XarrayBackend`/`KVBackend` or an in-memory backend, then test a selected Zarr/NetCDF backend separately. |

## Recovery order

1. Reproduce with a two-cell CPU fixture and print ordered coordinate keys,
   shapes, dtypes, and devices.
2. Validate the component's declared input/output mapping independently of its
   numerical core.
3. Check semantic axis and variable alignment, then check weights and units.
4. Add only the optional extra or backend required by the claimed feature.
5. Rerun the focused test and offline smoke check; then classify native,
   checkpoint, GPU, network, or credential tests separately.

Do not fix an unresolved failure by claiming broader support. Record an
unavailable backend, missing extra, unrun remote test, or unresolved coordinate
case in the handoff.
