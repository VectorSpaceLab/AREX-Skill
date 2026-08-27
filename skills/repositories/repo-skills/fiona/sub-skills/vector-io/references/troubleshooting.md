# Vector I/O troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `DriverError: unsupported driver` or unsupported mode | Driver is absent from the current GDAL build or Fiona's safe mode table | Inspect `fiona.supported_drivers`; use a compatible driver/mode or route to `environment-cloud` for installation diagnostics. Do not enable unsupported modes merely to suppress the error. |
| `SchemaError: no schema` / `no driver` | Write mode omitted required creation metadata | Supply `driver`, `schema`, and usually `crs`; use `src.profile` as a starting point for conversions. |
| Property write fails or becomes a string | Value does not fit the declared field type or target driver | Normalize values, adjust field type/width, write a tiny fixture, reopen, and compare `dst.schema`. |
| Output exists but has no features | Generator was consumed before `write`/`writerecords`, or the source cursor was exhausted | Reopen the source, avoid `list(src)` unless bounded, and verify the count after reopening the output. |
| `include_fields` and `ignore_fields` conflict | Both options were supplied | Choose one. Use `include_fields` for a whitelist and `ignore_fields` for a blacklist. |
| `DataIOError`, `FionaIOError`, or encoding errors | Wrong path, missing sidecar, unavailable format driver, or non-default encoding | Run a metadata probe, check all sidecar files, specify `encoding`, and verify the driver list. |
| MemoryFile says it is closed/immutable | It was closed, initialized with bytes and then opened for writing, or its lifetime ended | Use a context manager and choose either byte-backed read mode or empty write mode. |
| Iteration unexpectedly returns no rows | Collection cursor was already consumed | Reopen the collection; Fiona does not promise seeking back to the beginning. |
