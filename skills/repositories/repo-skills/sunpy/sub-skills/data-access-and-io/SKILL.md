---
name: data-access-and-io
description: "Choose SunPy data-access extras, build inspectable Fido queries,
  fetch remote records safely, and read or validate supported local solar-data
  formats."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 2-Clause
---

# SunPy data access and I/O

Use this route when the user needs to acquire solar data, inspect a Fido
search, manage sample/cache files, or read and write a supported file format.
Keep network access and file writes explicit: query construction is cheap and
local, but `Fido.search()` contacts providers and `Fido.fetch()` downloads and
writes files.

## Route the request

- **Remote search or download:** read
  [remote-data-workflows.md](references/remote-data-workflows.md). Build attrs
  first, inspect the response, and fetch only after the destination and network
  policy are clear.
- **A local file or format diagnostic:** read
  [file-formats.md](references/file-formats.md), then run
  [validate_local_data.py](scripts/validate_local_data.py) with a local path.
- **API names, signatures, extras, or response indexing:** read
  [api-reference.md](references/api-reference.md).
- **An exception, missing extra, proxy, credential, cache, or malformed file:**
  read [troubleshooting.md](references/troubleshooting.md).

Do not use this route for WCS construction, map transformations, plotting, or
map display; route those questions to [maps-and-visualization](../maps-and-visualization/SKILL.md).
Do not use it for coordinate-frame transformations or detailed time parsing;
route those to [coordinates-and-time](../coordinates-and-time/SKILL.md). A
request to analyze a `TimeSeries` object belongs to
[timeseries-and-solar-physics](../timeseries-and-solar-physics/SKILL.md), although
this route can explain how a file becomes a TimeSeries input.

## Minimal setup

Use the package environment's Python 3.12 and install only the capability set
needed by the workflow. The `net` extra enables the registered remote clients;
`asdf` enables ASDF serialization; `jpeg2000` enables JP2 support; `s3` adds
fsspec's S3 stack and is not part of `all`. A practical image/data setup is:

```bash
python -m pip install 'sunpy[net]'
# Add only when needed:
python -m pip install 'sunpy[asdf]' 'sunpy[jpeg2000]' 'sunpy[s3]'
```

Verify before doing work:

```python
import sunpy
from sunpy.net import Fido
print(sunpy.__version__, len(Fido.registry))
```

The current verified installation imports the core and all selected optional
modules, but optional codec behavior, S3 credentials, and provider availability
remain runtime-dependent. Never install a GPU stack for these CPU workflows.

## Workflow A: construct, inspect, then search

1. Define a bounded `a.Time(start, end)` and the narrowest common filters:
   `a.Instrument`, `a.Wavelength`, `a.Level`, `a.Sample`, `a.Physobs`,
   `a.Source`, or `a.Provider`.
2. Combine alternatives with `|` (or `a.AttrOr([...])`) and requirements with
   separate arguments or `&`. Parenthesize mixed `&`/`|` expressions.
3. To demonstrate or test query logic without network, use
   [print_fido_query.py](scripts/print_fido_query.py). It imports Fido but does
   not call `search` or `fetch`.
4. Call `Fido.search(*query)` only when network access is approved. Record
   `response.keys()`, `response.file_num`, each block's client, row count,
   `colnames`, `response.errors`, and `response.total_size()` where available.
5. Treat zero rows as a valid result, not as a fetch request. Tighten or relax
   one constraint at a time; if several providers answer, select a provider
   block explicitly before downloading.

## Workflow B: fetch to a controlled layout

Use `Fido.fetch(response, path=..., max_conn=..., progress=False,
overwrite=False)`. Pass a directory or a format string containing `{file}`;
for reproducibility prefer a project-local directory such as
`Path("downloads") / "{instrument}" / "{file}"`. Check the returned
`parfive.Results.data` paths and `.errors`. Do not fetch a whole broad response
just to discover its size.

A failed `Results` object can be retried with `Fido.fetch(previous_results)`;
all arguments must be retry results. Use a smaller response, a new explicit
path, proxy configuration, or provider-specific authentication rather than
blindly increasing concurrency. JSOC is credentialed and commonly needs a
registered email (`a.jsoc.Notify(...)`); never put that address or token in a
bundled example.

Supported registered client families include VSO, dataretriever sources,
JSOC, HEK, CDAWeb, SOAR, SOLARNET, and HELIO. Their availability and fields
are not interchangeable: use provider-specific attrs under `a.vso`, `a.jsoc`,
`a.hek`, `a.cdaweb`, `a.soar`, `a.solarnet`, and `a.helio` when the generic
attrs are insufficient. Read the provider matrix before asserting that a
query can be routed to one service.

## Workflow C: read or write locally

1. Preserve the original file and inspect its suffix and bytes. Run
   `validate_local_data.py path --header-only` for a non-destructive first pass.
2. For FITS use the public Astropy FITS reader for raw HDU/header inspection,
   and `sunpy.map.Map(path)` for a 2-D solar image. Map's unified reader
   dispatches supported FITS/JP2/ASDF inputs; inspect bytes and suffix before
   trusting a format, because a wrong suffix is not conversion.
3. Use the public special readers directly for
   `sunpy.io.special.genx.read_genx(path)` and
   `sunpy.io.special.srs.read_srs(path)`. Use `sunpy.io.ana.read()`/`write()`
   only when ANA is explicitly required; it is platform/C-extension
   constrained and deprecated.
4. For ASDF, use `map.save("result.asdf")` and then `sunpy.map.Map("result.asdf")`
   when the `asdf` extra is installed. Expect a loaded saved map to be a
   `GenericMap`; metadata, data, and mask are preserved, but custom map class
   registration affects subclass recovery.
5. Hand a successfully parsed time-series file to `TimeSeries` only for the
   construction step; route resampling, units, columns, and analysis to the
   sibling TimeSeries skill.

Validate outputs by checking the FITS HDU/header, special-reader return type,
array dimensions, table columns and metadata, or Map type/shape. For a safe
local fixture and optional FITS/ASDF round trip, use
[validate_local_data.py](scripts/validate_local_data.py) with no path or with
`--roundtrip fits|asdf`.

## Workflow D: sample data and managed files

`sunpy.data.sample.<NAME>` is a lazy sample-data path. Accessing a name may
 download a file; use `sunpy.data.sample.file_dict` to inspect
already-downloaded entries without downloading and avoid `download_all()` unless
the user explicitly accepts the bulk network/data cost. Sample files can be
passed to `Map` or a relevant `TimeSeries` factory.

`sunpy.data.manager` is a hash-verifying `DataManager`. A function decorated
with `@manager.require(name, urls, sha256, defer_download=True)` gets its file
via `manager.get(name)` when needed. The manager caches by hash and can detect
replacement or corruption. `override_file()` and `skip_hash_check()` are
controlled exceptions for local testing, not defaults for scientific results.
Set or inspect download/cache locations through SunPy configuration rather than
assuming the default home-directory paths. Read the data-manager section of
[remote-data-workflows.md](references/remote-data-workflows.md) before using a
remote sample or managed file.

## Stop and recover

Stop before download if the response is empty, provider errors are present,
the estimated size is unexpected, a credential is required, or the destination
is not writable. Use the decision tree in
[troubleshooting.md](references/troubleshooting.md): separate import/extra
problems from query/provider problems, then from file-layout/reader problems.
For remote examples in the source documentation, preserve them as
network-classified guidance only; this skill bundles no credentialed, GUI,
large-download, or unattended remote example.
