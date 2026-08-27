# Data-source troubleshooting

Classify the failure before retrying. A retry is useful for a transient remote
I/O error; it does not repair a bad lexicon, schema, coordinate, or tolerance.

## Variable and lexicon failures

### `KeyError` or a source-specific unsupported-variable error

**Likely cause:** the requested Earth2Studio ID is absent from the selected
source lexicon, or a compound native route cannot be resolved.

**Recover:**

1. Check membership in the selected lexicon before constructing a large
   request.
2. Confirm the ID's level suffix and standardized spelling (`t2m` versus a
   guessed native field name).
3. Select a source that advertises the variable, or add a tested lexicon/source
   mapping. Do not replace the ID with an arbitrary backend name.
4. Re-run a one-time, one-variable request before expanding the batch.

A variable present in a backend store is not automatically exposed by
Earth2Studio.

### Values have unexpected units or signs

**Likely cause:** a source lexicon modifier was skipped, applied twice, or the
same short ID represents a different accumulation/product convention.

**Recover:** inspect the lexicon mapping and modifier, then check a small
known-value fixture. Compare the standardized vocabulary description, source
product metadata, and output attributes where available. Do not fix units in a
post-hoc tensor transform unless the source contract explicitly requires it.

## Time and lead-time failures

### Exact local selection fails

`DataArrayFile`, `DataSetFile`, and multi-file local adapters use coordinate
selection. A request that is one minute away from a stored timestamp does not
become a match merely because it is close.

**Recover:** inspect `da.coords["time"]`, normalize the request to UTC, and
request one of the stored coordinate values. If nearest/interval selection is
needed, implement it explicitly in a wrapper or use a source that documents a
time tolerance; do not hide the mismatch with an unrelated lead time.

### Empty observation frame

**Likely causes:** the product file/cycle is unavailable, the requested
variable has no rows, timezone normalization moved the request, or no row
falls inside the source's tolerance window.

**Recover:** log the normalized request, source valid range, requested IDs,
row count, and tolerance bounds. Test a known source time and one variable.
For a scalar tolerance `tol`, the inclusive interval is `request ± tol`. For a
tuple `(lower, upper)`, it is `[request + lower, request + upper]`. A tuple
such as `(-1h, +6h)` is intentionally asymmetric; never convert it to
`±6h`.

### Invalid asymmetric tolerance

**Likely cause:** the tuple has the wrong length, is not a supported timedelta
type, or has `lower > upper`.

**Recover:** pass one `datetime.timedelta`, one `np.timedelta64`, or a tuple
of exactly two such values. Use a negative lower bound and positive upper
bound for a normal before/after window. Reject malformed configuration before
network access.

### Forecast values are shifted

**Likely cause:** initialization time and valid time were conflated, or a plain
DataSource was treated as a native ForecastSource.

**Recover:** inspect the source call signature. Native ForecastSource requests
receive `(time, lead_time, variable)`; plain sources receive `(time, variable)`.
For `fetch_data` with a plain source, verify that the requested valid times are
`time + lead_time`. For an inference output file, use `InferenceOutputSource`
only after filtering so either `time` or `lead_time` has length one.

## DataFrame schema failures

### Unknown field or invalid `fields` schema

**Likely cause:** a requested column is not in `source.SCHEMA`, or a supplied
`pa.Schema` uses a type that differs from the source schema.

**Recover:** print `source.SCHEMA.names` and compare field types, then request a
minimal valid subset. `fields=None` means all fields, not “infer arbitrary
columns.” Keep required metadata such as `time` and `variable` when matching
rows.

### DataFrame columns are present but variables are wrong

**Likely cause:** the source's observation/product lexicon maps standardized IDs
to native fields or product metadata, but caller code inspected only the
column names.

**Recover:** inspect both the lexicon and `df.attrs`; check the `variable`
column values and units. A generic `observation` column is not a universal
physical quantity.

## Local Xarray failures

### `DataArrayPathList` rejects a file

**Likely cause:** one file is missing one of `time`, `variable`, `lat`, or
`lon`, files have inconsistent coordinates/variables, a glob matches nothing,
or a file is unreadable.

**Recover:** open each file separately, inspect `dims`, coordinate names, and
variable labels, and make the files structurally consistent. Use
`DataArrayFile` for a single file that does not need the multi-file adapter's
spatial-dimension gate.

### `InferenceOutputSource` reports missing dimensions or both dimensions > 1

**Likely cause:** the Dataset has extra dimensions or was not filtered to one
ensemble/member/time/lead selection.

**Recover:** inspect Dataset dimensions and pass a `filter_dict` that selects
extra coordinates. After filtering, require `time`, `lead_time`, and
`variable`; keep one time or one lead. Do not flatten the array manually and
lose coordinate semantics.

### Local values are lazy, NaN, or wrong shape

**Likely cause:** the selection returned a lazy backend array, the file contains
missing values, or the source's coordinate order differs from assumptions.

**Recover:** inspect `da.dims`, `da.shape`, `da.coords`, dtype, and finite-value
count immediately after selection. Load only a tiny known slice for a smoke
check. Use named dimensions, not positional indexing.

## Optional dependencies and environment

### ImportError or optional-dependency guard

**Likely cause:** a remote product needs a package from the `data` extra or a
source-specific parser/client. The base package being importable does not
prove that every data adapter is ready.

**Recover:** identify the missing package from the exception and install the
smallest documented optional group in the active project environment. Keep
local Xarray/fixture checks separate from remote parser checks. Do not install
model extras just to validate a data source.

### CUDA conversion fails

`fetch_data(..., device="cuda", legacy=False)` needs CuPy. CUDA
`fetch_dataframe` needs CuPy and cuDF. If those are unavailable, use CPU or
use the legacy tensor path only when the Torch CUDA environment is verified.
Do not silently fall back to CPU when device placement is part of acceptance.

## Network, credentials, and cache

### Timeout, 403, DNS, or object-store errors

**Likely cause:** network policy, endpoint availability, missing credentials,
wrong cloud region/product permissions, or transient service failure.

**Recover:** first prove the request with a local fixture or a cached/staged
slice. Then test one time and one variable with a bounded timeout. Verify
credentials through the provider's supported mechanism, never by embedding
secrets in source code or command output. Check the source's cache setting and
cache directory permissions. Retry only transient failures; stop after the
configured retry/timeout budget.

Remote sources may cache downloaded chunks and may download substantial data
for broad requests. Use `cache=False` only when its documented cleanup
behavior is acceptable; it does not make a remote request offline.

### Async call hangs or behaves differently

Use the source's documented synchronous wrapper in ordinary scripts. In an
async application, call `await source.fetch(...)` and bound concurrency at the
caller. Do not nest event loops or assume every source implements `fetch`.
Retain the same time, variable, lead, and schema validation for either path.

## Utility and interpolation failures

### `fetch_data` rejects interpolation

A curvilinear source supports only `interp_method="linear"` in this helper.
`legacy=False` does not support `interp_to` at all. Correct the requested mode,
use a source-native grid, or perform a separately tested transformation.

### Tensor and coordinate map disagree

Check the DataArray before conversion, then inspect both the tensor shape and
returned coordinate mapping. Ensure spatial coordinates are not mistaken for
`time`, `lead_time`, or `variable`; for curvilinear arrays, check the 2-D
latitude/longitude arrays and any target `_lat`/`_lon` mapping.

## Minimal escalation record

When a failure cannot be resolved, record only the reproducible contract facts:
source class, source/lexicon IDs, normalized time and lead-time request,
tolerance bounds, requested fields/schema, local dimensions or remote product
route, optional dependency status, cache/network policy, exception type/message,
and the smallest request that reproduces it. This is enough to route the issue
without exposing credentials or dumping large data.
