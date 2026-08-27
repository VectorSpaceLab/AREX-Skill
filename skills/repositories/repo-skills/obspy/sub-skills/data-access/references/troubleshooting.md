# Data-access troubleshooting

| Symptom | Likely cause | Safe response |
| --- | --- | --- |
| Client construction fails with unknown shortcut or invalid URL | Provider alias is unavailable or base URL is malformed | Use a documented provider shortcut or a complete HTTP(S) URL. Run the planner first. Do not guess a new endpoint. |
| Client construction is slow or causes service-discovery errors | FDSN discovery contacts the endpoint by default | Use a finite timeout; `_discover_services=False` is an advanced opt-out that assumes default service parameters. Record that discovery was skipped. |
| `FDSNNoServiceException` | The selected provider does not expose the requested service | Choose a provider exposing `dataselect`, `station`, or `event`; do not retry the same service indefinitely. |
| `FDSNNoDataException` or empty result | Valid request has no matching data, or bounds/selector do not overlap availability | Keep the original query, check station availability or narrow filters, and report no data. Do not silently broaden wildcards. |
| 400 / invalid request | Unsupported parameter, malformed time/selector, or conflicting aliases | Validate UTC bounds, service-supported parameters, and blank location encoding. Inspect the planned query. |
| 401/403 or redirect warning | Credentials are needed, invalid, or unsafe across redirects | Ask the user to provide approved credentials through the runtime's secret mechanism. Never put credentials in this skill, planner output, or logs. |
| 413/414/request too large | Query window, wildcard, bulk list, or response is too large | Split by time/channel/provider and retain a manifest; never solve this by dropping time bounds. |
| 429 / 5xx / timeout | Rate limit, outage, gateway, or slow provider | Honor provider retry guidance, increase scope only deliberately, and use bounded retries outside this skill. Prefer cached/raw files for repeated experiments. |
| Routing returns no data after provider filters | Include/exclude filters removed all routed providers, or the router has no match | Inspect filters, remove only an intentionally restrictive filter, or use a direct known provider. Do not assume routing covers events. |
| Routing rejects `filename` or `attach_response` | Routing client does not support those direct-client options | Use direct FDSN clients or save/attach data in a separate explicit step. |
| SDS root is not a directory | Wrong local archive root or unavailable mount | Validate the path and permissions; stop. Never turn a local path failure into implicit network access. |
| SDS returns empty stream with missing day files | File not present, wrong SDS type, NSLC mismatch, or date path mismatch | Check the SDS layout, `sds_type`, `has_data()`, `get_all_nslc()`, and `get_availability_percentage()`. Missing files are gaps. |
| SDS data split at midnight | Records spill over daily boundaries or merge was disabled | Keep `fileborder_seconds`/`fileborder_samples` appropriate, inspect adjacent files, and choose `merge=-1`, `None`, or `0` deliberately. |
| SDS skips a tiny current file | A near-real-time file may still be written and is below MiniSEED size threshold | Wait for file finalization or report a transient local gap; do not infer remote unavailability. |
| TSIndex database path fails | SQLite index is missing/corrupt or is not a supported handler | Verify the database file, schema, and read permissions. Rebuild with `Indexer` only as a separately authorized archive operation. |
| TSIndex availability exists but read returns no traces | Indexed data path is stale or `datapath_replace` is wrong | Inspect a returned availability row and local path mapping; correct the explicit mapping. Do not fall back to FDSN silently. |
| TSIndex reports gap/overlap | Indexed timespans are discontinuous or overlapping | Use `get_availability(..., merge_overlap=True)`, preserve the reported gap policy, and validate `Stream.get_gaps()`. |
| SeedLink URL or connection rejected | URL lacks a host, uses unsupported scheme, or server is unreachable | Use `host:port`/`seedlink://host:port`, construct with `autoconnect=False`, then connect explicitly and handle the exception. |
| SeedLink `select_stream()` fails | Server lacks multi-station capability or stream selected after `run()` | Inspect `capabilities`, select streams before `run()`, and keep selectors finite. |
| SeedLink `run()` never returns | It is an intentional infinite streaming loop | Define a callback-owned stop condition, terminate/close the connection, and document the collection bound. |
| SeedLink capabilities XML cannot be parsed | Server returned malformed or unexpected INFO response | Record server response class and stop; do not fabricate capabilities or continue with unvalidated selectors. |

## Validation checklist

- Confirm UTC `starttime < endtime` and record the exact interval.
- Confirm provider/archive identity and whether access was direct, routed, local,
  or live.
- Confirm selectors after wildcard expansion and blank-location handling.
- For waveforms, record trace IDs, sample counts/rates, boundaries, and gaps.
- For local archives, record availability and missing-file behavior separately.
- For metadata, record object counts and requested level/format.
- Preserve exception type, provider message, and retry count without exposing
  credentials or private paths.
