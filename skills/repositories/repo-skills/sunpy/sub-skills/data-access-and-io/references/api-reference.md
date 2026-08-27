# Data-access API reference

This reference records the public API shape verified against the SunPy
inspection distribution `0.1.dev1+gd2ae0740e` on Python 3.12. It is a lookup
sheet, not a replacement for provider documentation.

## Installation and optional capability matrix

| Need | Extra/API | Limit |
|---|---|---|
| Fido and registered network clients | `sunpy[net]`, `from sunpy.net import Fido, attrs as a` | Searches contact external services; no provider SLA is implied. |
| FITS and common Map loading | core `sunpy.io`, `sunpy.map` | FITS metadata must describe a usable HDU; WCS interpretation is another route. |
| ASDF Map/coordinate serialization | `sunpy[asdf]`, `Map.save("x.asdf")`, `Map("x.asdf")` | Saved maps are serialized as `GenericMap`; custom class recovery is registration-dependent. |
| JPEG 2000 | `sunpy[jpeg2000]`, `sunpy.io`/`Map` | Requires `glymur` plus a system JPEG2000 codec; availability is platform-dependent. |
| S3/fsspec URIs | `sunpy[s3]` | Requires credentials/configuration and network; excluded from the base `all` extra. |
| Data-manager verification | core `sunpy.data.manager` | A hash and reachable URL are needed for a new managed file. |

The package metadata defines `core` as image/map/net/timeseries/visualization
extras and `all` as core plus ASDF, JPEG2000, OpenCV, SPICE, and scikit-image.
Adding `all` does not add S3 or Jupyter integration.

## Fido and attrs

Verified signatures:

```python
Fido.search(*query)
Fido.fetch(*query_results, path=None, max_conn=5, progress=True,
           overwrite=False, downloader=None, **kwargs)
a.Time(start, end=None, near=None)
a.Instrument(value)
a.Wavelength(wavemin, wavemax=None)
a.AttrOr(attrs)
```

Core attrs exposed by `sunpy.net.attrs` include `Time`, `Instrument`,
`Wavelength`, `Level`, `Sample`, `Detector`, `Resolution`, `Physobs`, `Source`,
`Provider`, and `ExtentType`. Attributes implement `&` and `|`; use
`a.AttrOr([...])` for a programmatically generated OR group. Provider-specific
attrs are registered under `a.vso`, `a.jsoc`, `a.hek`, `a.cdaweb`, `a.soar`,
`a.solarnet`, and `a.helio`. Dataretriever source attrs are exposed by their
source modules and generic attrs.

The current registry includes these client families:

| Family | Typical role | Provider-specific examples |
|---|---|---|
| VSO | Broad solar image/archive search | `a.vso.Filter`, `a.vso.PScale`, `a.vso.Pixels`, `a.vso.Quicklook` |
| dataretriever | Catalog/file sources such as GOES, LYRA, EVE, GONG, RHESSI, NOAA/SRS | source attrs such as `a.goes` |
| JSOC | HMI/SDO export and cutouts | `a.jsoc.Series`, `PrimeKey`, `Segment`, `Notify`, `Cutout` |
| HEK | Heliophysics events/features | `a.hek.EventType`, `a.hek.FRM.Name`, comparison wrappers such as `a.hek.FL.PeakFlux` |
| CDAWeb | Space-physics/mission datasets | `a.cdaweb.Dataset` |
| SOAR | Solar Orbiter archive | `a.soar.Sensor`, `Product`, `SOOP`, `Distance` |
| SOLARNET | Solar-data datasets | `a.solarnet.Dataset`, `Detector`, `Wavelength`, `Tags` |
| HELIO | Heliophysics catalogue tables | `a.helio.TableName`, `MaxRecords` |

`Fido.search` may return more than one provider block for one logical query.
The attribute names accepted by a client are not a guarantee that the remote
service has matching records.

## Unified responses and fetch

A `UnifiedResponse` is a sequence of `QueryResponseTable` blocks. Useful
non-network inspection is:

```python
response.keys()                 # provider names, lower-case, e.g. ["vso"]
response.file_num               # total records across blocks
response.errors                 # non-empty client error lists
response[0]                     # first provider block or block slice
response["vso"]                 # provider-name selection
response["vso", :2]             # first two rows from that provider
response.show("Start Time", "End Time")
```

A block exposes `.client`, `.colnames`, `len(block)`, `.show()`,
`.response_block_properties()`, and `.total_size()` when its client defines a
size column. `response.file_num == 0` is a normal empty-search outcome. Inspect
errors before fetching.

`Fido.fetch` returns `parfive.Results`. `path` can be a directory or a format
string and should include `{file}` when naming is important. If a plain
Directory/path is supplied, Fido appends `{file}`. `max_conn`, `progress`, and
`overwrite` control the downloader; `overwrite` accepts `False`, `True`, or
`"unique"`. A supplied `parfive.Downloader` takes precedence over those
settings. Retry only failed downloads by passing the resulting `Results` back
to `Fido.fetch`; do not mix retry results with query-response objects.

## Local I/O and integration

The public file-reader surface is the special-reader modules documented under
`sunpy.io.special` plus `sunpy.io.ana`; the lower-level unified dispatch used
internally by Map is not a stable public facade. Verified public signatures are:

```python
sunpy.io.special.genx.read_genx(filename)
sunpy.io.special.srs.read_srs(filepath)
sunpy.io.ana.read(filename, debug=False, **kwargs)
sunpy.io.ana.get_header(filename, debug=False)
sunpy.io.ana.write(filename, data, comments=None, compress=True, debug=False)
```

Use `astropy.io.fits.open(path, memmap=...)` for public raw FITS/HDU/header
inspection and `sunpy.map.Map(path)` for SunPy's higher-level FITS/JP2/ASDF
integration. Map's dispatch examines supported file content and suffixes and
requires at least one usable 2-D HDU. `sunpy.map.Map` accepts paths,
URLs/URIs, `(data, metadata)` pairs, and `GenericMap` objects; it can return a
single map, list, `MapSequence`, or `CompositeMap`. Use `allow_errors=True`
only when intentionally dropping bad inputs. `TimeSeries` has its own factory
and format-specific optional dependencies; pass the resulting local path to
that sibling workflow rather than using `sunpy.io` as a TimeSeries analysis
API.

## Sample data and manager

```python
import sunpy.data.sample as sample
sample.file_dict       # inspect cached paths without triggering sample downloads
sample.AIA_171_IMAGE   # lazy path access; may download that one sample

from sunpy.data import manager
@manager.require("name", ["https://example.invalid/file"], "<sha256>",
                  defer_download=True)
def function():
    return manager.get("name")
```

`DataManager.require(self, name, urls, sha_hash, defer_download=False)`
registers a hash-checked file, `get(name)` returns a `pathlib.Path`, and
`override_file`/`skip_hash_check` are context managers. The example URL above
is a placeholder: use a trusted, versioned source and a real SHA-256 hash in
application code, never in a generic bundled script.
