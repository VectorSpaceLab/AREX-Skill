# TimeSeries and solar-physics troubleshooting

Use this matrix after reading the relevant workflow. Error text can vary by
SunPy, pandas, Astropy, and reader versions; classify the failure by contract
rather than matching only a message.

| Symptom | Likely cause | Recovery and validation |
|---|---|---|
| `ImportError` or missing-dependency warning on `import sunpy.timeseries` | TimeSeries optional dependencies or pandas/matplotlib are not installed in the active environment | Install the documented SunPy TimeSeries extra in the active Python environment; verify `python -c 'import sunpy.timeseries, pandas, astropy'`. Do not install into a different interpreter. |
| `TimeSeries(dict_or_list, ...)` raises `NoMatchError` | Factory inputs are dispatch objects, not arbitrary numeric containers; a dict/list was expanded as inputs | Build `pd.DataFrame(values, index=pd.to_datetime(times))`, declare metadata and units, then call `GenericTimeSeries(df, meta, units)`. If passing multiple accepted groups, use tuples `(data, meta, units)`. |
| Factory reports `No types match` or `NoMatchError` for a file | Unknown file type, unsupported reader, ambiguous/missing instrument metadata, or missing `source=` | Check `Path.exists()`, file format, and header. Retry with the documented source selector only when the file is genuinely that source. If still unsupported, hand file-reader selection to `data-access-and-io`; do not force a wrong parser. `allow_errors=True` skips bad inputs with warnings and can return an empty list, which must not be analyzed. |
| Factory returns a list when one object was expected | Multiple files, CDF groups, or multiple accepted inputs were parsed | Inspect each element's class, columns, units, and range. Use `concatenate=True` only when the series are compatible and the desired result is one object. |
| DataFrame has no usable time range or `time_range` is `None` | Empty DataFrame or non-time index | Validate `len(df)`, `pd.to_datetime(df.index)`, monotonicity, and timezone policy before construction. An empty result is not a valid observation. |
| `Unknown units for <column>` warning | A column is absent from the units mapping | Add the correct Astropy unit before analysis. Inspect `ts.units`; the fallback dimensionless unit is not evidence about the measurement. |
| CDF warns about unknown units or an expected variable is empty | CDF unit spelling is not in SunPy's mapping, or the file contains an empty variable | Preserve the original unit string. Register an explicit Astropy unit with `u.def_unit`/`u.add_enabled_units` or apply a documented conversion. Verify `quantity(name).unit`, shape, and finite values. Do not guess `#/cc`, `deg K`, or similar strings. |
| CDF import fails because `cdflib` is missing | Optional CDF dependency is not installed | Install/enable the CDF extra, then rerun an import smoke. If the environment cannot provide it, keep CDF as unavailable and use a local FITS/CSV/DataFrame path instead. |
| GOES/EVE/FERMI/LYRA local file does not dispatch | Source-specific parser needs explicit source or file product differs from supported form | Use `source="XRS"`, `"EVE"`, `"ESP"`, `"GBMSummary"`, or `"LYRA"` as appropriate. Validate expected columns and units. Do not use a selector merely to silence an error. Unsupported products should be routed to I/O/file-reader guidance. |
| Source-specific series has unexpected columns or all NaNs | Product generation, quality flags, missing-value sentinel, or parser-specific convention differs | Inspect `meta`, columns, units, raw-value range, and quality columns. Confirm the mission product documentation and record the missing-value policy before filtering or interpolation. |
| `to_table()` loses the time column or unit | Confusion between DataFrame index and output Table schema, or a non-unit-bearing raw column | Expect `date` as the first table column. Check `table.colnames`, `table["date"]`, and each `table[col].unit`. Reconstruct with one primary time index when reading back. |
| Truncation returns no rows | Requested range lies outside the series or string bounds cannot be parsed | Print `ts.time_range`, use `TimeRange`/`parse_time`-compatible bounds, and check start <= end. Validate non-empty output before plotting. |
| Truncation or concatenation metadata looks stale | Returned object was not used, or metadata was manually mutated | Assign the returned series (`new_ts = ts.truncate(...)`). Inspect `new_ts.meta.to_string()` and the data range. Reconstruct only with matching metadata and units. |
| `concatenate(..., same_source=True)` raises `TypeError` | Source classes differ | Use `same_source=True` only when class/source identity is required. Otherwise concatenate intentionally and accept a generic output, then validate mixed columns and metadata. |
| Duplicate timestamps remain or values conflict after concatenation | Overlapping files or pandas concat policy | Inspect and sort the resulting index; define a documented duplicate policy and apply it to a copied DataFrame. Never silently choose a duplicate when both measurements are scientifically meaningful. |
| `resample()` is missing on TimeSeries | SunPy exposes no dedicated TimeSeries resample method in this release | Call pandas on `ts.to_dataframe()`, select an aggregation, then reconstruct with metadata and units. Check whether aggregation preserves units and whether metadata ranges need updating. |
| `plot()`/`peek()` fails with an empty-data error | The series has zero rows after filtering/truncation or a loader produced no data | Check shape and time range. Repair the input/range; do not bypass the validation. |
| Plot hangs, opens a GUI, or fails on CI | Interactive backend or browser invocation | Set `MPLBACKEND=Agg`, pass an explicit `axes`, save to a temporary/output file, close the figure. Use `plot()`, not `quicklook()`, in headless runs. |
| `solar_rotate_coordinate()` says observer/time are invalid | Both or neither keyword supplied; observer has no `obstime`; observer is a string | Supply exactly one. For `observer`, pass a frame/SkyCoord with `obstime`. For `time`, expect the Earth-observer warning. Route frame construction to coordinates-and-time. |
| Rotation model raises `ValueError` | Misspelled model | Use exactly `howard`, `snodgrass`, `allen`, or `rigid`. Record `frame_time` as `sidereal` or `synodic`. |
| Rotation calculation has unit errors or implausible scale | Duration/latitude were passed as bare numbers or degrees/radians were confused | Pass `duration` as `u.s`/`u.day` and latitude as `u.deg`. Check the returned `Longitude` in degrees and compare a known deterministic smoke value. |
| `differential_rotate()` fails on a map | Wrong route/input, missing scikit-image, or entirely off-disk map | Hand map/WCS creation and diagnosis to `maps-and-visualization`. Confirm the map is not entirely off disk and install the optional dependency if this map operation is required. |
| A remote GOES/HEK example cannot run | Network, service availability, credentials, or a large download is unavailable | Do not retry as a local TimeSeries bug. Use `data-access-and-io` for bounded search/fetch, then pass a downloaded local path here. The bundled scripts intentionally do not access remote services. |

## Difficult-case acceptance checks

1. **Wrong factory container**: prove that a dict/list is rejected or does not
   create the intended object; recover with a DataFrame and assert columns,
   shape, units, and range.
2. **Unknown CDF unit/reader**: use a local fixture or mocked reader result,
   capture the warning, and assert that the unresolved column is explicitly
   dimensionless or explicitly registered before calculation. If `cdflib` or a
   representative CDF fixture is unavailable, record the gap rather than
   claiming CDF verification.
3. **Headless empty plot**: truncate beyond the data range, assert the expected
   empty-data failure, then use an in-range subset with `Agg` and assert a
   returned/saved figure.
4. **Rotation contract**: assert that both/neither observer/time fails, a
   valid quantity-aware model returns an angular result, and an invalid model
   fails with `ValueError`.
