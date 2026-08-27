# Route and Log API Reference

## Core identifier classes

Verified signatures:

```text
LogReader(identifier: str | list[str], default_mode=ReadMode.RLOG, sources=None, sort_by_time=False, only_union_types=False)
Route(name, data_dir=None)
SegmentRange(segment_range: str)
SegmentName(name_str: str, allow_route_name=False)
save_log(dest, log_msgs, compress=True)
```

`ReadMode` values:

| Value | Meaning |
| --- | --- |
| `r` | read rlogs only |
| `q` | read qlogs only |
| `a` | auto: prefer rlogs and fall back to qlogs |
| `i` | auto-interactive: ask before qlog fallback |

## Route and segment syntax

Valid forms include:

```text
344c5c15b34f2d8a|2024-01-03--09-37-12
344c5c15b34f2d8a/2024-01-03--09-37-12
344c5c15b34f2d8a|2024-01-03--09-37-12--5
344c5c15b34f2d8a/2024-01-03--09-37-12/5
344c5c15b34f2d8a/2024-01-03--09-37-12/4:6/q
344c5c15b34f2d8a/2024-01-03--09-37-12/-1/r
```

`SegmentRange.seg_idxs` may need an API call when the range omits an endpoint, such as `/1:` or `/-1`. Validate the string first if network access is not available.

## Local vs remote routes

`Route(name, data_dir=...)` scans local directory layouts for rlogs/qlogs/cameras. Without `data_dir`, it calls comma API route-file endpoints and may need authentication.

`LogReader` accepts:

- Direct local file paths.
- Direct URLs.
- Route/segment/range identifiers resolved through internal, comma API, openpilotci, or comma car segment sources.
- A list of identifiers, which are concatenated in iteration order.

Use `sort_by_time=True` when merging sources where event order matters. Use `only_union_types=True` when corrupted or non-union Event messages could break `which()` calls.

## Basic patterns

```python
from openpilot.tools.lib.logreader import LogReader, ReadMode

lr = LogReader("344c5c15b34f2d8a/2024-01-03--09-37-12/0/q", default_mode=ReadMode.QLOG)
first_cp = lr.first("carParams")
alerts = list(lr.filter("onroadEvents"))
```

`LogReader.filter("carState")` yields the union payload (`msg.carState`) rather than whole `Event` messages. When you need timestamps or multiple message types, iterate over raw messages and inspect `msg.which()`.

## Cache and source notes

- `COMMA_CACHE` changes the download cache root.
- `DISABLE_FILEREADER_CACHE=1` disables URLFile cache behavior.
- Missing rlogs can fall back to qlogs only in auto modes.
- Large route ranges can load many segments; prefer qlogs and narrow ranges for first-pass triage.
