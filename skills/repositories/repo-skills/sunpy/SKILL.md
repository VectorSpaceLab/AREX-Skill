---
name: sunpy
description: "Use SunPy for solar-physics data access, time and coordinate
  transformations, Map/WCS image analysis, file I/O, TimeSeries, visualization,
  and solar-physics calculations."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 2-Clause
---

# SunPy operating router

Use this skill when a task names **SunPy** or asks for Python workflows involving
solar observations, FITS/WCS solar images, heliographic coordinates, Fido data
searches, GOES/EVE/CDF time series, or solar constants and rotation. SunPy is a
CPU-oriented scientific-Python package; do not add a GPU stack unless another
package in the user's workflow independently requires it.

## First route

1. Establish the package version and installation variant. SunPy requires
   Python 3.12 or newer in this source baseline. For example, install only the
   routes needed with `python -m pip install 'sunpy[map,net,timeseries]'` in an
   isolated environment. Read [installation and configuration](references/installation-and-configuration.md)
   for the complete extras matrix, configuration directories, logging, and a
   private smoke check.
2. Identify whether the input is a local file, an in-memory object, or remote
   data. Treat network access, credentials, sample-data downloads, and output
   directories as explicit decisions.
3. Load only the focused route below. Keep this root as routing and
   cross-cutting guidance; detailed APIs and troubleshooting live in the linked
   references.

| User request | Read next |
|---|---|
| Parse times, construct/transform HPC/HGS/HGC frames, ephemerides, or track a solar feature | [coordinates-and-time](sub-skills/coordinates-and-time/SKILL.md) |
| Build/load/save a Map, repair FITS/WCS metadata, crop/reproject/plot images, or use sequences/composites | [maps-and-visualization](sub-skills/maps-and-visualization/SKILL.md) |
| Build a Fido query, search/fetch a provider, manage sample/cache files, or diagnose a FITS/ASDF/GENX/SRS file | [data-access-and-io](sub-skills/data-access-and-io/SKILL.md) |
| Build/analyze a TimeSeries, load local GOES/EVE/CDF data, calculate solar constants or differential rotation | [timeseries-and-solar-physics](sub-skills/timeseries-and-solar-physics/SKILL.md) |
| Diagnose installation, optional imports, configuration, or a package-wide failure | Read [troubleshooting](references/troubleshooting.md) and [compatibility](references/compatibility.md) |

## Cross-cutting rules

- Keep the original data and metadata intact. Make a copy before repairing
  headers or changing units, and record the source, observation time, observer,
  and assumptions in the result. For a complete local Map-plus-TimeSeries
  example, read [integrated local pipeline](references/integrated-local-pipeline.md).
- Prefer explicit units (`astropy.units`) and explicit times. Validate shape,
  finite values, WCS/frame metadata, units, and output paths before scientific
  interpretation.
- Use local/in-memory fixtures for smoke checks. Never call `sunpy.data.sample`
  attributes, `download_all()`, `Fido.search()`, or `Fido.fetch()` merely to
  test an import; those can access the network.
- For remote work, build and inspect a bounded query first, then approve the
  provider, size, credentials, destination, and retry policy. A successful
  query is not evidence that a download is safe or complete.
- Optional modules warn or fail when their extra is absent. Install the narrowest
  extra that owns the requested capability instead of using `sunpy[all]` by
  habit. Read the route's troubleshooting reference when an import fails.
- In headless environments set `MPLBACKEND=Agg`, create/close figures
  explicitly, and save to a user-approved path. Do not use `peek()`,
  `quicklook()`, or interactive examples as unattended verification.

## Safe package smoke

After selecting an environment, run the bundled [SunPy smoke helper](scripts/sunpy_smoke.py):

```bash
python scripts/sunpy_smoke.py --help
python scripts/sunpy_smoke.py
```

It imports the selected public modules and exercises tiny local time, frame,
Map/WCS, and GenericTimeSeries operations without remote data. It is not a
substitute for the route-specific checks or for validating a provider/backend.

## Scope limits

This skill covers SunPy core's public user workflows. It does not teach
maintainer release/CI tooling, benchmark interpretation, source-test editing,
private service credentials, unattended bulk downloads, interactive GUI
operation, or a mission's scientific calibration pipeline. SPICE kernels,
provider availability, native codecs, and external ephemeris services remain
optional runtime conditions; state them rather than silently falling back.

For package-wide install/import/configuration failures, read
[troubleshooting](references/troubleshooting.md). For version-sensitive extras
and supported workflow variants, read [compatibility](references/compatibility.md).
The source baseline and evidence paths are recorded in
[repo provenance](references/repo-provenance.md).
