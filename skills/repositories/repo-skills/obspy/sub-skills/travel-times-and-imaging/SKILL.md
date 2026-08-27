---
name: travel-times-and-imaging
description: "Teaches a Researcher to compute ObsPy TauP arrivals, ray paths,
  pierce points, geodetic distances, azimuths, and headless waveform, spectrum,
  beachball, and optional map visualizations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Travel times and imaging

Use this skill when the task asks for theoretical seismic arrivals, ray geometry,
source/receiver geodesy, or a reproducible scientific figure. Keep the input
coordinates, model, phases, units, plotting backend, and output filenames in the
analysis record. This skill is offline by default: it does not retrieve data or
open a GUI.

## Route the request

- **Arrivals only:** use `TauPyModel.get_travel_times` with source depth (km),
epicentral distance (degrees), and an explicit `phase_list` such as `['P', 'S']`.
- **Model ray geometry:** use `get_ray_paths` for sampled `path` points, or
`get_pierce_points` for model-boundary/additional-depth intersections.
- **Latitude/longitude input:** use `locations2degrees` for a spherical great-
circle distance, or `gps2dist_azimuth` for WGS84 distance in metres plus forward
and reverse azimuths. The `TauPyModel.*_geo` methods convert coordinates to a
TauP distance; they still calculate travel time/path on a spherical model.
- **Figures:** use `Arrivals.plot_rays`/`plot_times`, `plot_ray_paths`, or
`plot_travel_times` for TauP; `Stream.plot`/`Trace.plot` for waveforms;
`Trace.spectrogram` or `obspy.imaging.spectrogram.spectrogram` for spectra;
and `obspy.imaging.beachball.beachball` for focal mechanisms. Use `show=False`
(or `MPLBACKEND=Agg`) and an explicit `outfile` for automation.
- **Map request:** route to the optional Cartopy path described in
[geodetics and imaging](references/geodetics-and-imaging.md). Do not make a map
a prerequisite for ordinary plots.

## Minimal procedure

1. Validate latitude in `[-90, 90]`, normalize/document longitudes, and state
whether depth is below the surface in km. Do not silently treat metres as km.
2. Instantiate one shipped model, normally `TauPyModel(model='iasp91')`; model
loading is comparatively expensive. Reuse it for multiple queries.
3. Pass a bounded phase list. Inspect `len(arrivals)`, each `arrival.name`,
`arrival.time` (seconds), `arrival.distance` (degrees), and the relevant
`path`/`pierce` record array before plotting or selecting an arrival.
4. Save figures to a caller-owned output directory. Close figures created by
matplotlib after saving when running batches. Never overwrite an input or an
existing result without explicit permission.
5. Record model, source/receiver coordinates, depths, phase list, distance
convention, optional-dependency status, and output-file existence/size.

## Public API quick contract

| Need | Public call | Output/validation signal |
|---|---|---|
| Time | `TauPyModel.get_travel_times(...)` | `Arrivals`; arrival time is seconds |
| Path | `get_ray_paths(...)` | `arrival.path` fields `p,time,dist,depth` |
| Pierce | `get_pierce_points(..., add_depth=[...])` | `arrival.pierce` record array |
| Geographic time/path | `get_travel_times_geo` / `get_ray_paths_geo` | geographic distance/azimuth metadata when supported |
| Distance/azimuth | `locations2degrees` / `gps2dist_azimuth` | degrees, or `(metres, azimuth, backazimuth)` |
| Waveform | `stream.plot(outfile=..., show=False)` | non-empty image; input remains unchanged |
| Spectrum | `trace.spectrogram(samp_rate=..., outfile=..., show=False)` | non-empty image; window must fit data |
| Focal mechanism | `beachball([strike,dip,rake], outfile=...)` | non-empty image or bytes with `format=` |

See [taup-models.md](references/taup-models.md) for phase/model/depth details,
[geodetics-and-imaging.md](references/geodetics-and-imaging.md) for plotting
recipes and optional Cartopy behavior, and
[troubleshooting.md](references/troubleshooting.md) for recovery. Run the
bundled offline helper for a tiny end-to-end check:

```bash
python scripts/taup_and_plot_smoke.py --help
MPLBACKEND=Agg python scripts/taup_and_plot_smoke.py --output-dir ./obspy-imaging-smoke
```

The helper creates only its selected output directory, uses shipped model data
and synthetic samples, and reports whether Cartopy is available without trying
to download map data.

## Boundaries and handoff

- Route waveform filtering, detrending, merging, resampling, and triggers to
`waveform-processing` or `signal-analysis`; this skill only plots/inspects
waveforms in support of imaging.
- Route reading/writing waveform, event, inventory, and image metadata to
`formats-and-metadata`.
- Route FDSN, routing, SDS, and all live retrieval to `data-access`.
- TauP is a 1-D spherical velocity-model calculation. It is not a locator,
full-wave solver, or a replacement for observed arrival picking.
- Cartopy map rendering and geographiclib-enhanced path coordinates are
optional capabilities. A missing optional dependency is a reportable result,
not a reason to make the CPU/headless workflow fail.
