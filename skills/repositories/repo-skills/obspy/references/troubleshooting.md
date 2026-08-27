# ObsPy cross-cutting troubleshooting

## Install and import

- **`obspy` cannot import or a native module is missing:** check Python version, platform wheel/build support, NumPy/SciPy compatibility, compiler availability for a source install, and `python -m pip check`. Reinstall the public package in a clean isolated environment rather than mutating an unrelated environment. Verify `obspy`, `obspy.io.mseed`, `obspy.signal`, and `obspy.taup` separately.
- **A package import works but a feature fails later:** ObsPy loads many plugins lazily. Run the smallest operation for the selected route: a local MiniSEED read/write, signal filter, or TauP arrival. Keep the traceback and exact format/backend path; do not claim all plugins from a top-level import.
- **Optional import error for Cartopy, pyshp, or geographiclib:** install the corresponding documented extra only if the task requires it. Ordinary waveform plots, core geodesy, and CPU signal workflows must not be made dependent on Cartopy.

## Data and API validation

- **Empty or unexpected result:** distinguish no data from a malformed selector or service response. For local data inspect file headers and object counts; for FDSN inspect the provider, UTC bounds, NSLC selectors, and service-specific exception before retrying.
- **Wrong object type or write error:** `read`/`Stream.write` handle waveforms; `read_events`/`Catalog.write` handle catalogs; `read_inventory`/`Inventory.write` handle station metadata. Use an explicit format and do not treat a waveform as a catalog or inventory.
- **Timing or gap mismatch:** check `starttime`, `endtime`, `sampling_rate`, `delta`, `npts`, masks, and `get_gaps()` before filtering or merging. Copy before mutations and state the fill/interpolation policy.
- **Response correction fails:** load a real response-bearing Inventory/RESP or a justified PAZ. Missing response metadata is a hard prerequisite failure; never infer it from a channel name.

## CLI and network boundaries

- **CLI not found or flags differ:** run the installed command's `--help` and use the public Python API if the entry point is unavailable. Do not point to scripts from a source checkout.
- **FDSN timeout, authentication, 204/no-data, or request-too-large:** reduce the bounded time window/query, verify provider and credentials policy, and use the exact service exception. Do not retry an authentication or malformed-query error indefinitely.
- **SeedLink/streaming hangs:** `run()` is intentionally unbounded. Define connection, callback, timeout, stop, and close ownership before dispatch; plan first with the no-network query helper where applicable.

## Output and plotting

- **Plotting fails in a headless worker:** set `MPLBACKEND=Agg` before importing pyplot, use `show=False`, and save to a fresh caller-owned file. Missing Cartopy affects map plots only.
- **Conversion appears successful but loses meaning:** reopen the output and compare fields supported by the target format. Preserve StationXML/RESP alongside waveform data and preserve QuakeML when event metadata is richer than a legacy target.
- **Stale skill guidance:** compare the current package's version, public entry points, plugin table, and major modules with [repo provenance](repo-provenance.md). If they differ, refresh the repo skill instead of extending stale claims.
