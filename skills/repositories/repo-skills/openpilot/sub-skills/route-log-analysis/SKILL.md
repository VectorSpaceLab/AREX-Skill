---
name: route-log-analysis
description: "Guides openpilot route identifiers, qlog/rlog access, LogReader
  APIs, message filtering, event summaries, and route-cache troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# route-log-analysis

Use this sub-skill when a task involves openpilot route IDs, segment ranges, qlogs/rlogs, `LogReader`, `Route`, `SegmentRange`, `logMessage`, alerts/events, CAN messages, route cache/source behavior, or local-vs-remote log access.

## Read first

- [references/route-and-log-api.md](references/route-and-log-api.md) for route identifier grammar and verified API signatures.
- [references/log-analysis-workflows.md](references/log-analysis-workflows.md) for summaries, filters, qlog/rlog decisions, memory/size analysis, and process handoff.
- [references/troubleshooting.md](references/troubleshooting.md) for malformed identifiers, missing logs, auth/network/cache, corrupted capnp messages, and heavy route handling.

## Bundled helpers

- [scripts/check_route_identifier.py](scripts/check_route_identifier.py): validate and normalize a route/segment/range string without downloading logs.
- [scripts/summarize_route_events.py](scripts/summarize_route_events.py): summarize events, alerts, cameras, and duration from a provided route/log when openpilot is installed.
- [scripts/filter_openpilot_logs.py](scripts/filter_openpilot_logs.py): filter `logMessage`, `errorLogMessage`, and `operatingSystemLog` records by level.

## Workflow

1. Normalize the route selector first. A task may use `dongle|timestamp`, `dongle/timestamp`, `--segment`, `/segment`, ranges such as `/4:6`, and selectors `/q` or `/r`.
2. Decide whether the user has local files or needs remote route access. Remote routes may require authentication and network/cache space.
3. Prefer `qlog` for quick event/alert/fingerprint scans; use `rlog` when full message fidelity is required.
4. Keep analysis finite: avoid loading large videos, all segments, or route ranges without a reason.
5. Route CAN/FW fingerprint results or process-replay validation to [car-ports-and-controls](../car-ports-and-controls/SKILL.md).
6. Route live service timing or Params/msgq behavior to [core-services-and-runtime](../core-services-and-runtime/SKILL.md).

## Validation choices

Good CPU-safe checks are route string parsing, synthetic local qlog reads, help/parser checks for bundled scripts, and selected `openpilot/tools/lib/tests` cases. Skip route downloads, account-only routes, GUI replay, and process-replay reference downloads unless prerequisites and time budget are explicit.
