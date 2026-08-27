# Data-access and I/O troubleshooting

Use the first matching row, collect the exact exception and path, and do not
turn a remote or optional-dependency failure into a format claim. The goal is a
recoverable diagnosis with the smallest change.

## Decision matrix

| Symptom | Likely class | Check | Recovery |
|---|---|---|---|
| `import sunpy.net` warns or fails | Missing/broken `net` extra | `python -m pip show sunpy`; `from sunpy.net import Fido` | Install `sunpy[net]` in the active Python, then run `pip check`; do not mix environments. |
| ASDF import/conversion fails | Missing/incompatible optional reader | `import asdf`; check `sunpy[asdf]` | Install the ASDF extra; if optional support is unavailable, use FITS and record the loss of ASDF-only mask/object fidelity. |
| JP2 reader unavailable | `glymur`/codec missing | `import glymur`; inspect codec error | Install `sunpy[jpeg2000]` and a supported codec, or obtain FITS; do not rename JP2 to FITS. |
| ANA reader import error | Native C extension/platform issue | `from sunpy.io import ana`; inspect the exception | Use a supported Linux/macOS build or convert externally; ANA is deprecated and unsupported on Windows. |
| `No module named ...` after install | Wrong interpreter | `python -c 'import sys; print(sys.executable)'` and `pip -V` | Install with `python -m pip` from the exact interpreter used to run SunPy. |
| Local byte/suffix check disagrees | Unsupported/corrupt/wrong file | Inspect first bytes and suffix; run local validator | Request the correct format, use a specific supported reader only when content is known, or stop. |
| FITS/Map returns no usable data | Empty/unsupported HDU or reader mismatch | Check HDU count and shape | Inspect headers; select a valid FITS HDU or use the format's special reader. |
| `Map` raises no 2-D HDU/metadata error | File is not a Map input | Check array dimensionality and required metadata | Use `sunpy.io` for raw data, or provide a real Map-compatible header; route WCS repair to map skill. |
| `read_srs` fails while FITS works | Text layout is not SRS | Check section headers and issued metadata | Use the correct SWPC SRS report or a format-specific parser; do not force Map loading. |

## Fido query and response failures

| Symptom | Check | Recovery |
|---|---|---|
| `Fido.search` raises `NoMatchError` | Query attrs and provider registration; look for a missing `|` around alternatives | Start with `a.Time` plus one generic attr, then add constraints. Use provider-specific attrs under the correct namespace. |
| Search returns no records and no errors | Time/product/provider coverage and overly narrow filters | Expand time or remove one filter at a time. Keep the original empty query in the run log. |
| Search returns several provider blocks | `response.keys()`, block client names, row counts, and `response.errors` | Select `response["provider", rows]` explicitly or constrain with `a.Provider`/provider attrs. |
| Search returns a partial block with errors | `response.errors` and the affected block | Do not fetch that block blindly. Retry after checking service/proxy/provider status or select a healthy block. |
| `Fido.fetch` says path is not writable | Parent directory permissions and path expansion | Choose a project-local writable directory, create it deliberately, and keep `{file}` in the format. |
| Files overwrite unexpectedly | `overwrite` and path collision | Default to `overwrite=False`; use `"unique"` for parallel products, then validate duplicate identity. |
| Fetch fails transiently | `Results.errors`, network/proxy/TLS/DNS, rate limits | Retry the `Results` object once or with a bounded policy; reduce rows/connections or fix proxy. Never retry a query result as a download result. |
| Fetch asks for credentials | Provider policy (often JSOC) | Obtain user-approved credentials through the provider's supported runtime path; never hard-code email/token in the skill. |
| Returned file has an unexpected suffix/layout | Provider product selection or partial download | Check `Results.data`, file size, magic bytes, and headers before passing to Map/TimeSeries. |

Fido's `Fido.fetch` defaults are `max_conn=5`, `progress=True`, and
`overwrite=False`; a supplied `parfive.Downloader` changes those controls. For
JSOC-only requests SunPy limits connections/splits internally. A network retry
cannot repair an invalid query or a corrupt remote product.

## Data, cache, proxy, and configuration failures

- **Sample path triggered an unexpected download:** accessing
  `sunpy.data.sample.NAME` is lazy but network-capable. Use
  `sample.file_dict` to inspect cache state first; do not use
  `sample.download_all()` as a probe.
- **Managed hash mismatch:** the cached file may be stale, changed remotely, or
  corrupted. Let `DataManager` redownload through its normal hash path and
  compare the reported SHA-256. Use `override_file(..., sha_hash=...)` only for
  a controlled, documented fixture. Do not make `skip_hash_check()` permanent.
- **Cache appears in the wrong directory:** inspect SunPy's `[downloads]`
  configuration and the current interpreter's config, rather than assuming a
  home-directory location. Keep cache/database changes separate from analysis
  outputs.
- **Proxy/DNS/TLS error:** confirm the environment proxy variables and CA
  bundle, test the provider endpoint with the approved network policy, and
  retry with a narrow request. A local offline query test does not validate
  remote access.
- **S3 URI cannot open:** install the S3 extra and configure credentials in the
  external runtime. Do not put credentials in an `fsspec_kwargs` literal in
  reusable skill code. If S3 is unavailable, stage a local copy and validate
  its bytes before reading.

## API misuse and format mismatch

- `a.Wavelength` requires a value (and optionally a second bound); use Astropy
  units where ambiguity matters. `a.Time` needs a start and optional end.
- Mixed `&`/`|` expressions need parentheses. Python's `and`/`or` are not query
  operators and can discard an attr object.
- `UnifiedResponse` can be indexed by one or two indices only. Use
  `response["vso", :2]`, not a three-index expression. A provider-name lookup
  may fail when no such client answered.
- `Fido.fetch` accepts a UnifiedResponse, response table/row, or all-Results
  retry arguments. Do not pass file paths back to `fetch` as though they were
  query results.
- The public special readers do not share one generic return type: use
  Astropy FITS/HDU APIs for raw FITS, `sunpy.io.special.genx.read_genx` for
  nested dictionaries, `sunpy.io.special.srs.read_srs` for a QTable, and
  `sunpy.io.ana.read` for ANA pairs. Do not call `.data` or Map methods on the
  wrong return type.
- A wrong suffix can be corrected only after byte/header inspection. Renaming
  a file is not conversion and may make later debugging harder.

## Recovery record

For a reproducible handoff, record: SunPy version/interpreter, installed extra,
query expression, provider blocks and errors, selected rows, destination
format, file byte/shape/header checks, and whether network or credentials were
skipped. If an optional reader or remote provider could not be verified, state
that limit explicitly rather than claiming full format/provider coverage.
