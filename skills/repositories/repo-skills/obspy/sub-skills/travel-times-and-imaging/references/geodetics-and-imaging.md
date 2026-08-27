# Geodetics and scientific imaging

## Geodetic validation

Use degrees for latitudes/longitudes and validate latitude bounds before calling
geodetic routines. `locations2degrees` is vector-friendly spherical geometry:

```python
import numpy as np
from obspy.geodetics import locations2degrees, gps2dist_azimuth

lat1 = np.array([36.12, 0.0])
lon1 = np.array([-86.67, 0.0])
lat2 = np.array([33.94, 0.0])
lon2 = np.array([-118.40, 10.0])
degrees = locations2degrees(lat1, lon1, lat2, lon2)
metres, azimuth, backazimuth = gps2dist_azimuth(36.12, -86.67,
                                                 33.94, -118.40)
```

`gps2dist_azimuth` uses geographiclib when available and otherwise falls back
to ObsPy's Vincenty implementation. The fallback has known near-antipodal
limitations and may warn or return a safe fallback. `geographiclib` is an
optional geodetic dependency; do not assert that a geographic path has latitude
and longitude fields unless the runtime capability probe confirms it.

## Waveform and spectrum figures

A `Stream`/`Trace` is expected to be constructed or obtained by the waveform
workflow first. Plot it without changing samples:

```python
import matplotlib
matplotlib.use("Agg")
from obspy import Stream, Trace
import numpy as np

tr = Trace(data=np.sin(np.linspace(0, 8*np.pi, 2000)))
tr.stats.sampling_rate = 100.0
tr.plot(outfile="waveform.png", show=False)
tr.spectrogram(samp_rate=tr.stats.sampling_rate, wlen=2.0,
               outfile="spectrogram.png", show=False)
```

`Stream.plot`/`Trace.plot` accept the plotting options documented by ObsPy,
including `outfile`, `format`, `show`, `handle`, `type`, and `automerge`.
`Trace.spectrogram` delegates to the public spectrogram function and fills in
sampling rate from trace metadata when omitted. `wlen` is in seconds and the
input must be long enough for at least the FFT window and multiple windows;
`per_lap` is an overlap fraction in `[0, 1)` in normal use. Plotting makes a
copy of the stream for its internal work; still verify the caller's samples
when a non-mutation guarantee matters.

Avoid using a remote example URL in a reproducibility run. Use a local trace or
a deterministic synthetic fixture, and write to a temporary/caller-selected
output directory. Check `Path(outfile).is_file()` and `stat().st_size > 0`.

## Focal mechanisms / beachballs

`obspy.imaging.beachball.beachball` draws either a strike/dip/rake triple or
six independent moment-tensor components. The strike is clockwise from north,
dip is measured from horizontal, and rake follows the focal-plane convention.
For a direct single-file output:

```python
from obspy.imaging.beachball import beachball

beachball([150.0, 87.0, 1.0], outfile="focal-mechanism.png")
# Or receive bytes instead of writing a file:
pdf_bytes = beachball([150.0, 87.0, 1.0], format="pdf")
assert pdf_bytes.startswith(b"%PDF")
```

`beach(...)` returns a Matplotlib collection for composition into an existing
axes; `beachball(...)` creates/uses a figure and supports `outfile`, `format`,
`fig`, `facecolor`, `bgcolor`, `nofill`, and `plot_zerotrace`. Close figures in
batch jobs. Validate the mechanism shape (3 or 6 values) before calling.

## Optional Cartopy maps

`obspy.imaging.maps.plot_cartopy(lons, lats, size, color, ...)` creates a map
scatter plot and supports `projection='global'`, `'ortho'`, and `'local'` plus
Cartopy projection instances. The map implementation is optional and requires
Cartopy at a compatible version. Cartopy may also need Natural Earth boundary
data on first use; data acquisition is outside this skill's offline smoke
path. `obspy.core.util.CARTOPY_VERSION` or an import probe can be used to report
availability.

A safe optional branch is:

```python
try:
    from obspy.imaging.maps import plot_cartopy
except (ImportError, RuntimeError) as exc:
    print("Cartopy map unavailable:", exc)
else:
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    plot_cartopy([0.0, 10.0], [0.0, 5.0], [30, 30], [1, 2],
                 projection="local", show=False, ax=ax)
    fig.savefig("map.png")
    plt.close(fig)
```

Do not silently replace a requested map with a non-geographic scatter plot. If
Cartopy is unavailable, report the optional dependency and keep ordinary
waveform/TauP/beachball plots as the successful baseline. Do not download map
data, credentials, or network data as part of a smoke check.

## Evidence boundary

This reference adapts public APIs from `obspy.geodetics`, `obspy.imaging`,
TauP/imaging tests, and tutorial snippets. It excludes network-backed example
retrieval and unverified Cartopy/shapefile execution from required behavior.
