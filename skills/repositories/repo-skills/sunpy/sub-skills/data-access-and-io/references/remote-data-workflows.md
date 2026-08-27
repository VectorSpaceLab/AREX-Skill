# Remote-data workflows

SunPy separates query construction from network execution only at the user
workflow level: building attrs and importing Fido is local, while
`Fido.search()` and `Fido.fetch()` are network-capable operations. Keep a
query, response summary, selected rows, destination, and retry state together
so an interrupted run can be resumed without silently broadening the request.

## 1. Build a bounded query locally

```python
import astropy.units as u
from sunpy.net import Fido, attrs as a

time = a.Time("2020-01-01T00:00:00", "2020-01-01T00:01:00")
channels = a.Wavelength(171 * u.angstrom) | a.Wavelength(193 * u.angstrom)
query = time & a.Instrument.aia & channels
print(query)       # local object construction; no service is contacted
print(Fido)        # local registry/client listing
```

Use `a.AttrOr([a.Wavelength(w * u.angstrom) for w in values])` for a dynamic
list. Use `&` for constraints that must all apply, and `|` for alternatives;
parenthesize every mixed expression. `a.Sample` limits cadence when the
provider supports it. `a.Physobs`, `a.Level`, `a.Source`, `a.Provider`,
`a.Detector`, or provider-specific attrs should be added only when the target
service documents them.

[print_fido_query.py](../scripts/print_fido_query.py) is the offline fixture
for this stage. It accepts a time range, instrument, and wavelengths and
prints the expression plus registered client names without searching.

## 2. Search only after approval

```python
from pathlib import Path
from sunpy.net import Fido, attrs as a

response = Fido.search(
    a.Time("2020-01-01", "2020-01-01T00:01:00"),
    a.Instrument.aia,
    a.Wavelength(171, 171),
)
print(response.keys(), response.file_num, response.errors)
for block in response:
    print(block.client.__class__.__name__, len(block), block.colnames)
    print(block.show())
    print(block.total_size())
```

The response is a `UnifiedResponse` containing one `QueryResponseTable` per
provider/query block. It can be indexed by integer/slice, provider name (for
example `response["vso"]`), or a two-index tuple. Provider names are not a
promise that every returned row is downloadable. Check `file_num`, row count,
columns, estimated size, and `errors` before selecting rows.

Decision tree for zero or many results:

1. `file_num == 0` and no errors: the constraints may be too narrow, the
   service may not cover that time/product, or the provider has delayed
   indexing. Change one constraint and search again; do not fetch.
2. `errors` is non-empty: preserve the provider error, check the optional
   `net` extra, proxy/TLS/DNS, service status, and provider-specific syntax.
   A partial response is not an all-clear.
3. Multiple blocks or unusually many rows: select the provider and rows
   explicitly (`response["vso", :2]`, for example), or add an appropriate
   source/provider/instrument constraint. Estimate file size first.

## 3. Provider choice and special constraints

- **VSO:** broad image/archive searches usually use `a.Time`, `a.Instrument`,
  `a.Wavelength`, `a.Physobs`, and optional `a.vso` fields such as pixels,
  scale, filter, or quicklook. VSO records can include multiple providers and
  products for one logical request.
- **dataretriever:** source-specific clients cover products such as GOES,
  LYRA, EVE, GONG, RHESSI, NOAA indices/predictions/SRS, NoRH, and related
  catalogs. Use the source's attrs and expect product-specific response
  columns and download endpoints.
- **JSOC:** use `a.jsoc.Series`, `PrimeKey`, `Segment`, `Protocol`, `Keyword`,
  `Cutout`, and `Notify` as appropriate. Export requests often require a
  registered email; credentials and email values must be supplied by the user
  at runtime, not stored in a skill or command history. JSOC fetches use one
  connection by default in Fido's JSOC-only path.
- **HEK:** query events with `a.Time`, `a.hek.EventType`, and optional HEK
  comparison wrappers. HEK results are event tables, not image files. The
  `hek2vso` bridge can translate a HEK event to VSO attrs, but a matching VSO
  record is not guaranteed.
- **CDAWeb:** use `a.cdaweb.Dataset` with a time range. Results often lead to
  time-series-compatible files and require the relevant TimeSeries optional
  reader for later analysis.
- **SOAR:** use `a.soar.Sensor`, `Product`, `SOOP`, or `Distance` with a time
  range. Wavelength search coverage is product-dependent; some instruments do
  not expose wavelength metadata.
- **SOLARNET:** use dataset/detector/wavelength/tags attrs. Archive indexing
  and product formats vary, so inspect the returned columns rather than
  assuming Map or TimeSeries compatibility.
- **HELIO:** use `a.helio.TableName` and optionally `MaxRecords`. This is a
  catalogue/table workflow, not a generic image query.

The client registry is extensible and data availability changes remotely. The
provider notes above are routing hints, not claims that a particular date or
product exists.

## 4. Fetch safely and resume

```python
from pathlib import Path

selected = response["vso", :2]
out = Path("project-downloads") / "{instrument}" / "{file}"
result = Fido.fetch(selected, path=out, max_conn=2, progress=False,
                    overwrite=False)
print(result.data)
print(result.errors)
```

The path is expanded and the `{file}` token is retained as the downloaded
basename. `overwrite=False` avoids replacing an existing file; use
`overwrite="unique"` when duplicate names must coexist. A plain directory is
also accepted, but an explicit format prevents accidental mixing of providers.
Validate that every path in `result.data` is inside the intended output tree,
exists, has a plausible suffix, and can be opened locally before analysis.

If some downloads fail, save or retain the `parfive.Results` object and retry
with `Fido.fetch(result)`. Do not mix `Results` and query responses in the same
retry call. When failures persist, reduce the selection, use a smaller
`max_conn`, set proxy variables/configuration used by the environment, or
switch to a documented provider endpoint. Avoid unbounded retry loops.

Network, proxy, authentication, service status, rate limiting, and remote
file-layout errors cannot be proven by a local smoke test. Record them in the
run log and classify them separately from reader failures.

## 5. Sample data and remote data manager

Accessing one `sunpy.data.sample.NAME` path may download that sample lazily.
Use `sample.file_dict` to inspect cache state without downloading, and avoid
`sample.download_all()` unless a complete sample set is intentional. Sample
paths are ordinary local paths after retrieval and can be passed to Map or a
TimeSeries constructor.

The global `sunpy.data.manager` is intended for application/test functions
whose remote input is versioned by SHA-256:

```python
from sunpy.data import manager

@manager.require(
    "calibration",
    ["https://trusted.example/calibration.dat"],
    "<known-sha256>",
    defer_download=True,
)
def load_calibration():
    path = manager.get("calibration")
    return path
```

Use a real trusted URL and a verified hash in a real application. The manager
caches by hash, detects a missing or changed cached file, and can retry a
replacement. `override_file(name, local_path_or_uri, sha_hash=...)` is useful
for a controlled local fixture. `skip_hash_check()` should be a temporary,
explicit testing decision, never the default for a scientific input.

## Documentation-only exclusions

Examples requiring a live provider, JSOC email, remote sample download, bulk
archives, credentials, or a GUI are intentionally not bundled as executable
helpers. They remain represented here as guarded workflows. A user who needs
one must approve network/credential use, choose an explicit destination, and
validate the downloaded file layout before loading it.
