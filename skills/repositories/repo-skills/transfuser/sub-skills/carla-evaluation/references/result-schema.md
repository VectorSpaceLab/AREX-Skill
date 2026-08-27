# Leaderboard Result Schema

## Purpose

Use this reference to interpret or validate checkpoint JSON without importing
CARLA. The schema describes files written by the repository's leaderboard
checkpoint and statistics utilities.

## Top-Level Shape

```json
{
  "sensors": ["carla_camera", "carla_lidar"],
  "values": ["74.487", "82.710", "0.894"],
  "labels": ["Avg. driving score", "Avg. route completion", "Avg. infraction penalty"],
  "entry_status": "Finished",
  "eligible": true,
  "_checkpoint": {
    "progress": [36, 36],
    "records": [],
    "global_record": {}
  }
}
```

`labels` and `values` are parallel arrays. Values are normally formatted numeric
strings. The full output has three score labels followed by nine infraction
labels.

`_checkpoint.progress` is `[next_route_index, total_route_executions]`. The
first element is incremented after a route and is the resume position. Total
executions equal XML route count multiplied by repetitions.

## Per-Route Record

Each entry in `_checkpoint.records` contains:

| Field | Shape | Meaning |
|---|---|---|
| `route_id` | string | Usually `RouteScenario_<xml-id>` |
| `index` | integer | Execution index, including repetitions |
| `status` | string | `Completed` or a failure string |
| `scores.score_route` | number | Route completion percentage in `[0, 100]` |
| `scores.score_penalty` | number | Multiplicative infraction penalty |
| `scores.score_composed` | number | `max(score_route × score_penalty, 0)` |
| `meta.duration_system` | number | Wall-clock seconds |
| `meta.duration_game` | number | Simulator seconds |
| `meta.route_length` | number | Planned route length in metres |
| `infractions` | object of arrays | Human-readable event descriptions |

Expected infraction keys are:

```text
collisions_pedestrian
collisions_vehicle
collisions_layout
red_light
stop_infraction
outside_route_lanes
route_dev
route_timeout
vehicle_blocked
```

Descriptions may include coordinates such as
`(x=20.03, y=109.45, z=0.253)`. Coordinate text is useful for CSV and map
output but is not guaranteed for every event. `outside_route_lanes`
descriptions must preserve the off-route distance if aggregate off-road
percentage is to be recomputed.

## Global Record

`_checkpoint.global_record` has the same route-record shape, conventionally
with `route_id: -1` and `index: -1`. Its scores are averages over the evaluator's
configured total route executions. Its infraction fields are scalar rates, not
per-event arrays.

The global record is evaluator output, while the bundled parser recomputes
aggregate infraction rates from per-route records. Prefer the parser's result
when comparing runs assembled from multiple JSON files.

The source statistics implementation accumulates global infraction rates route
by route rather than dividing total event count by aggregate driven distance.
The bundled parser instead follows the repository result-parser calculation:
total event count divided by total driven kilometres. These quantities need not
match, so always state which one is reported.

## Status And Eligibility

Common lifecycle values include:

- Top-level `entry_status`: empty, `Started`, `Rejected`, `Crashed`, `Finished`,
  `Finished with missing data`, or `Finished with agent errors`.
- Per-route `status`: `Started`, `Completed`, `Failed`, or
  `Failed - <reason>` such as blocked, timeout, setup failure, agent crash, or
  simulation crash.

`eligible` is primarily a completeness gate. The writer sets it false when
records or progress are missing, but `Finished with agent errors` can remain
eligible. Therefore:

1. Check `progress[0] == progress[1]`.
2. Check record count against total executions.
3. Inspect every route status.
4. Check `entry_status` and `eligible`.
5. Inspect score and infraction fields.

Do not use only one of these signals.

## Known Source Quirk

The global-statistics code compares route status to `Completed` using object
identity rather than value equality. A global `meta.exceptions` list can
therefore contain records whose route status text is actually `Completed`.
Treat per-route `status` as authoritative and use `global_record.meta.exceptions`
only as a diagnostic hint.

## Validation Commands

Human-readable inspection:

```bash
python scripts/inspect_result_json.py /path/to/result.json --records
```

Machine-readable inspection:

```bash
python scripts/inspect_result_json.py /path/to/result.json --format json
```

Strict success gate:

```bash
python scripts/inspect_result_json.py /path/to/result.json --strict
```

Strict mode rejects incomplete progress and any non-`Completed` route. Normal
mode validates structure while reporting failed or partial routes as warnings.
Use [longest6-and-results.md](longest6-and-results.md) for aggregation policy.
