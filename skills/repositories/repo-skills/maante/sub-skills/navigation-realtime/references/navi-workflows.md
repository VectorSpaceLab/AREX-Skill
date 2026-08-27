# Navigation Workflows

## Local Route Navigation

Pipeline custom action: `local_route_navigation`.

Python class: `LocalRouteNavigation(context, route_json=None, *, tolerance=5.0, angle_backend="auto", position_backend="map", frame_interval=0.1, debug=False)`.

Important methods verified from source/inspection:

```python
navigator.load_route_json(route_json)
navigator.run_route(route_json=None, *, route_name="", segment_index=1) -> bool
navigator.close()
```

Use class form when one Python action must run multiple segments without reinitializing map locator/angle predictor. Use Pipeline action form for ordinary single-segment route nodes.

Pipeline parameter example:

```json
{
  "json_path": "penquan",
  "route_name": "penquan",
  "segment_index": 1,
  "frame_interval": 0.1,
  "tolerance": 5,
  "angle_backend": "auto",
  "position_backend": "auto",
  "debug": false
}
```

`json_path` may be absolute/relative; if not found directly, the runtime searches under the resource routes directory and can add `.json`.

## Online Map Navigation

Pipeline custom action: `online_map_navigation`.

Task options load config from attach nodes:

- `OnlineMapNavigationSettingsConfig`: `port`, `tolerance`, `frame_interval`.
- `OnlineMapNavigationPositionBackendConfig`: `position_backend`.
- `OnlineMapNavigationAngleBackendConfig`: `angle_backend`.
- `OnlineMapNavigationDebugConfig`: `debug`.

Default service URL:

```text
ws://127.0.0.1:14514
```

The server binds `0.0.0.0`, but user-facing clients normally connect to localhost. It broadcasts state and can receive route updates from an online map client.

State message shape:

```json
{
  "type": "navi-state",
  "version": 1,
  "position": {
    "x": -134394.56,
    "y": 199913.53,
    "z": 11416.17,
    "pixelX": 4090,
    "pixelY": 6750,
    "sourceWidth": 11264,
    "sourceHeight": 11264,
    "score": 1.0,
    "mode": "coordinate"
  },
  "angle": 123.4,
  "pitch": 0.0,
  "angleConfidence": 0.96,
  "route": {"waypoints": [], "active": false, "currentIndex": 0, "status": "idle"},
  "timestamp": 1770000000.0
}
```

When coordinate data is temporarily unavailable, the service may publish stale coordinates with a mode that indicates staleness. When no position can be converted, `position` is `null`.

## Position Backends

- `map`: use visual map matching and angle predictor.
- `coordinate`: require coordinate capture backend; fail if unavailable.
- `auto`: try coordinate capture first and fall back to visual map positioning if coordinate capture cannot start.

Coordinate capture tries packet/capture backends such as pcap/scapy and pktmon. It requires the packaged Windows coordinate module, matching Python ABI, and suitable permissions/services.

## Angle Backends

- `auto`: choose available backend.
- `directml`: Windows DirectML inference.
- `cpu`: CPU inference.

A CPU import check does not prove DirectML. Keep backend-specific claims explicit.

## Map Teleport

Custom action: `map_teleport_to_point`.

Parameters:

- `teleport_point_id` or `teleport_id`: required target id.
- `teleport_points_file`: default `map_teleport/teleport_points.json`.
- `template_threshold`: default 0.8.
- `ocr_threshold`: default 0.5.
- `max_area_switches`: default 15.
- `action_delay`: default 0.5 seconds.

Teleport point records include id/name, area name, icon index, selection name, icon path, and optional description.

## Teleport Required Check

Custom action: `check_teleport_required`.

It can load a named target point, locate current position, compute distance, and run map teleport when far from the target. Relevant parameters include:

- `point_id`
- `teleport_point_id`
- `position_backend`
- `coordinate_type`
- `coordinate_timeout`
- `threshold`
- `debug`

The decision object records current point, target point, distance, whether teleport is needed, mode, and coordinate type.

## Calibration Workflow

MaaNTE has a maintainer script that fits raw coordinate samples to map pixels and updates generated constants in the coordinate position module. Use it only when intentionally recalibrating source constants. It requires at least three non-collinear calibration points and a maximum RMS error threshold. Keep this as a maintainer workflow, not an automatic runtime check.

## Realtime Assistance

The `RealTime` task uses a looping custom action that repeatedly runs a configured holder node containing enabled realtime branches such as auto loot, skip-story, and auto teleport. It must continue until `context.tasker.stopping` is true. Changes to branch enablement should go through task options and Pipeline nodes, not hard-coded Python lists unless that is the requested design.

## Dataset Collection

`AutonomousDrivingDatasetRecorder` records screenshot sequences and WASD labels for a bounded duration. It writes timestamped session directories under a configured output directory and uses a fixed label map for none, A, D, W, S, AW, AS, DW, DS. It depends on Windows key-state APIs for actual labeling.
