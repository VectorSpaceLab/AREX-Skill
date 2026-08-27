# Log Analysis Workflows

## Event and alert summary

For a quick route triage, count `onroadEvents`, alert transitions from `selfdriveState.alertType`, camera-state message counts, and route duration. Use qlogs first unless full rlogs are required. The bundled `summarize_route_events.py` helper adapts the repo's event-counting workflow with finite output and explicit errors.

## Log message filtering

`logMessage` and `errorLogMessage` payloads are JSON strings. Filter by `levelnum` and print file/line/function/message when present. `operatingSystemLog` records can contain JSON or raw OS log text. Use the bundled `filter_openpilot_logs.py` helper for portable filtering.

## Qlog size and memory analysis

The repo has scripts that compute per-message compressed qlog contribution and memory usage from `procLog`/`deviceState`. These are useful but may require full route loads, matplotlib, or demo-route downloads. Keep them optional; for first-pass agent work, report message counts and suspicious high-volume types before producing plots.

## CAN and fingerprint handoff

When the route task turns into CAN/FW/VIN fingerprint extraction, switch to the car-port sub-skill. It owns fingerprint formatting, FW ambiguity, and car interface test selection.

## Process replay handoff

When a user asks to run a process against route logs or compare outputs to references, switch to the car-port sub-skill's process replay reference. Process replay can download reference logs, start managed processes, write new logs, and take significant CPU time.

## Safe local synthetic verification

A generated or test fixture qlog can validate:

- `LogReader` direct file parsing.
- `first()` and `filter()` semantics.
- `SegmentRange` parsing independent of remote APIs.
- Handling corrupted or non-union messages with `only_union_types=True`.

Synthetic cases do not replace required remote-route or full replay validation when the task specifically depends on route data from comma servers.
