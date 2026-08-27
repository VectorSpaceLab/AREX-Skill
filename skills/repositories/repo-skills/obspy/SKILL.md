---
name: obspy
description: "Guides seismological data workflows with ObsPy, including waveform
  processing, format conversion, event and station metadata, FDSN or local
  archive access, signal analysis, travel times, geodesy, and headless imaging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ObsPy operating skill

Use this skill when a task names ObsPy or asks to read, process, convert,
retrieve, analyze, or visualize seismological waveforms, events, station
metadata, or travel times. It is a reusable package guide: first inspect the
installed ObsPy version and the task's local/network boundaries, then load only
the focused route below.

## Install and inspect

Install the public package in an isolated supported Python environment:

```bash
python -m pip install obspy
python -c "import obspy; print(obspy.__version__)"
```

The base runtime uses NumPy, SciPy, Matplotlib, lxml, SQLAlchemy, requests,
and decorator. Add only needed extras: `obspy[tests]` for focused test tooling,
`obspy[geo]` for geographiclib, `obspy[imaging]` for Cartopy map plots, and
`obspy[io.shapefile]` for shapefile support. Do not install `all` by default.
ObsPy includes native extensions for several IO and signal/TauP paths; if an
import fails, read [cross-cutting troubleshooting](references/troubleshooting.md)
before changing package versions.

For a minimal read-only smoke check, run
[`scripts/check_environment.py`](scripts/check_environment.py). It verifies
public imports, native extension handles, a TauP calculation, headless plotting,
and CLI help without contacting a service or writing into the current directory.

## Route by the user's deliverable

| User request or artifact | Read next | Primary entry points |
|---|---|---|
| Read/write, inspect, trim, merge, filter, resample, or plot local waveforms | [`waveform-processing`](sub-skills/waveform-processing/SKILL.md) | `read`, `Trace`, `Stream`, `UTCDateTime` |
| Convert MiniSEED/SAC/ASCII, QuakeML, StationXML, RESP/SEED/XSEED; preserve metadata | [`formats-and-metadata`](sub-skills/formats-and-metadata/SKILL.md) | `read`, `read_events`, `read_inventory`, `Catalog`, `Inventory` |
| Query FDSN waveforms/stations/events, route providers, use SDS/TSIndex/SeedLink | [`data-access`](sub-skills/data-access/SKILL.md) | `Client`, `RoutingClient`, filesystem clients |
| Filter/detect/trigger/correlate, remove or simulate responses, PPSD, arrays, realtime | [`signal-analysis`](sub-skills/signal-analysis/SKILL.md) | `obspy.signal`, `Trace`/`Stream` methods, `obspy.realtime` |
| Compute arrivals/ray paths, geodesy, beachballs, spectra, or scientific figures | [`travel-times-and-imaging`](sub-skills/travel-times-and-imaging/SKILL.md) | `TauPyModel`, geodetics, imaging, Matplotlib |

A task can load multiple routes. For example, retrieve with `data-access`,
serialize with `formats-and-metadata`, then process with `waveform-processing`
or `signal-analysis`.

## Shared operating rules

1. Make the data boundary explicit: local file, synthetic fixture, local
   archive, or live network service. Do not turn an offline task into a network
   request implicitly.
2. Preserve raw inputs and write fresh outputs by default. ObsPy processing
   methods commonly mutate `Trace`/`Stream`; copy before destructive transforms.
3. Record UTC bounds, NSLC identifiers, sample rate, units/response status,
   format, parameters, output path, and validation checks.
4. Prefer explicit format names and bounded query windows. Check returned
   object counts, gaps/overlaps, metadata, and output re-openability rather than
   accepting a successful call at face value.
5. Use `MPLBACKEND=Agg`, `show=False`, and explicit output files for headless
   plotting. Treat Cartopy, shapefile, credentials, and live service access as
   optional prerequisites, not silent fallbacks.

## Public boundaries and refresh

This graph covers user-facing package workflows, public CLIs, and representative
CPU/offline behavior. It does not cover maintainer release automation, docs
deployment, large benchmark/training operations, or every legacy file format.
Read [provenance](references/repo-provenance.md) when working from a checkout
or deciding whether this graph is stale; refresh it when the package version,
public entry points, or major source evidence differ.
