# Troubleshooting travel-time and imaging workflows

| Symptom | Likely cause | Recovery and validation |
|---|---|---|
| `TauPyModel` cannot load a model | Typo, unsupported model name, or invalid custom `.npz` path | Start with shipped `iasp91` or `ak135`; list the exact model and inspect the exception. Do not guess a custom path. |
| No arrivals returned | Phase is unavailable at the distance/depth, phase list is too restrictive, or distance is outside the useful branch | Retry a known-good `P` query at the same depth/distance; inspect `len(arrivals)`; then add requested phases one at a time. Empty is not an arrival-time zero. |
| TauP phase/model error | Invalid phase grammar or incompatible phase for the model | Use a simple phase (`P`, `S`, `PP`) to isolate the model, then validate the requested phase name. Preserve the exception text in the report. |
| Incorrect results by a factor of 1,000 | Metres supplied as km or seconds interpreted as minutes | State units at every boundary: source/receiver depth km, distance degrees, arrival time seconds, `gps2dist_azimuth` distance metres. Convert deliberately. |
| Geographic `*_geo` path lacks lat/lon points | `geographiclib` is absent or below the supported version | Continue to use travel times or model-coordinate paths; report the warning. Install a compatible optional geographiclib only if geographic path coordinates are required. |
| Latitude validation fails | Latitude is outside `[-90, 90]` | Correct the input; do not clamp silently. Normalize/document longitudes separately. |
| Near-antipodal geodesy warning or instability | Vincenty fallback limitations when geographiclib is unavailable | Install/enable geographiclib for robust WGS84 inverse calculations, or report the fallback limitation. Compare units and azimuth convention before accepting values. |
| Ray plot raises an axes warning/error | `plot_type='spherical'` was sent to an ordinary axes, or Cartesian to a polar axes | Create `plt.subplots(subplot_kw={'projection': 'polar'})` for spherical; use ordinary `plt.subplots()` for Cartesian. Pass `show=False` in automation. |
| `plot_travel_times` / `plot_ray_paths` is slow | Large distance range, many phases, or large `npoints` | Bound phase list and `npoints`; reuse one `TauPyModel`; save a lower-resolution diagnostic first. |
| Headless run hangs or backend error | Matplotlib selected an interactive backend | Set `MPLBACKEND=Agg` before importing plotting modules, pass `show=False`, save to a file, and close the figure. |
| Empty waveform plot fails | Empty `Stream` or `Trace` | Confirm at least one trace and finite data; route construction/loading to waveform-processing. |
| Spectrogram reports signal too short | `wlen`/FFT window does not fit the sample count or yields fewer than two time bins | Increase fixture length or reduce `wlen`; ensure sampling rate is positive and `per_lap` is sensible. Do not pad silently without recording it. |
| Output file missing/zero bytes | Wrong output directory, figure not saved, or a backend error | Use an explicit writable path, call `savefig`/`outfile`, assert file and size, then close. Never overwrite an existing result without permission. |
| Beachball rejects input | Focal mechanism is not 3 or 6 values, contains nonnumeric data, or has wrong convention | Validate `[strike, dip, rake]` or six tensor components and document the coordinate convention. Try a known-good `[150, 87, 1]` fixture. |
| Map warns Cartopy is unavailable | Optional `[imaging]` dependency is not installed | Report “optional map path unverified/unavailable”; ordinary plots remain the required baseline. Do not install or download map data implicitly. |
| Map fails on first render | Cartopy boundary data or compatible projection dependency is missing | Keep map verification optional; report the dependency/data requirement and use a non-map plot for offline evidence. |

## Diagnostic sequence

1. Run a package/import check and `MPLBACKEND=Agg` headless check.
2. Compute a simple `iasp91` `P` arrival at depth 10 km and distance 35°.
3. Compute one WGS84 geodesy tuple and one spherical degree distance.
4. Generate a ray/path or travel-time plot, then a deterministic waveform and
beachball file; assert non-empty outputs.
5. Only after the baseline passes, try the requested phase, model, geography,
or optional map. Keep each changed input isolated.

## Strict limits

This skill does not diagnose source-repository modifications, perform live FDSN
requests, retrieve Cartopy data, or infer a scientific interpretation from a
plot. Route those needs to the owning sub-skill or require explicit external
setup.
