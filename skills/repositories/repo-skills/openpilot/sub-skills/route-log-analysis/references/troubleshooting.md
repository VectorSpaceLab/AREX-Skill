# Route and Log Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `AssertionError: Segment range is not valid` | malformed route/segment/range selector | Run `check_route_identifier.py`; normalize `dongle|timestamp` or `dongle/timestamp` before adding `/segment` or `/slice/q`. |
| API call while only parsing | Range omitted endpoint (`/1:`, `/-1`) and needs max segment count | Use explicit start/end slices when offline, or allow route metadata access. |
| `LogsUnavailable` | route not uploaded, inaccessible, qlogs/rlogs missing, source fallback exhausted | Try a qlog selector `/q`, verify auth/public access, narrow segment range, or use local files. |
| Unauthorized comma API | missing/expired auth token | Authenticate only if the user approves account-backed access; otherwise use public/local route data. |
| Slow or huge memory use | broad route range, rlogs/video, plotting scripts | Narrow segments, use qlogs, stream/filter messages, avoid cameras unless needed. |
| `pycapnp.KjException` or corrupted events | corrupted log bytes or non-union Event | Use `only_union_types=True`, isolate segment, and report skipped corrupt messages. |
| Cache confusion | `COMMA_CACHE`, default cache, or `DISABLE_FILEREADER_CACHE` changed | Inspect cache env vars and avoid deleting caches unless asked. |
| Plot/replay requested from log task | GUI/binary/display/video requirements | Route to simulator-and-visual-tools and first decide if a text summary is enough. |

When the route analysis produces car fingerprints, missing signals, safety mismatches, or process replay tasks, switch to car-ports-and-controls rather than continuing generic log triage.
