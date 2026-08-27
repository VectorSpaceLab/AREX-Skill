---
name: navigation-realtime
description: "Guides MaaNTE map teleport, local route navigation, online map
  WebSocket, coordinate capture, realtime assistance, movement tests, and
  dataset collection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Navigation and Realtime

## Use This When

Use this sub-skill for MaaNTE's realtime and navigation systems:

- `RealTime` auto loot / skip-story / auto teleport loops.
- `OnlineMapNavigation` WebSocket service and route ingestion.
- `local_route_navigation` CustomAction and `LocalRouteNavigation` Python class.
- Map teleport and teleport-required distance checks.
- Coordinate capture backends, route JSON schemas, map calibration, and route validation.
- Movement tests and autonomous-driving dataset collection.

If the task is only a gameplay task that happens to call navigation (for example fountain or FishNew auto-navigation), read this for the navigation portion and return to [../gameplay-tasks/SKILL.md](../gameplay-tasks/SKILL.md) for task-specific behavior.

## Read First

1. [references/navi-workflows.md](references/navi-workflows.md) for local route navigation, OnlineMapNavigation, coordinate capture, and map teleport APIs.
2. [references/route-data-formats.md](references/route-data-formats.md) for route and teleport JSON schemas.
3. [references/troubleshooting.md](references/troubleshooting.md) for DirectML/CPU, coordinate backend, WebSocket, and route-convergence failures.
4. Use [scripts/validate_route_json.py](scripts/validate_route_json.py) to validate route JSON without a game window.

## Core Runtime Boundaries

- Visual position backend uses screenshots, map template matching, and the ONNX angle predictor.
- Coordinate backend uses an encrypted Windows coordinate module plus packet/capture backend and can skip visual screenshot work when active.
- Online map navigation and route following share one custom action because MaaFramework runs one action at a time.
- Route execution needs a live Maa `Context`, controller, current game state, and stopping signal; it cannot be fully unit-tested from an ordinary script.

## Safe Static Checks

```bash
python sub-skills/navigation-realtime/scripts/validate_route_json.py path/to/route.json
python ../../scripts/check_maante_environment.py --summary
```

These checks validate data shape and imports only. They do not prove that coordinate capture, DirectML inference, game movement, or WebSocket clients work in a real run.

## Editing Priorities

- Keep route parsers permissive only where source code supports it: `pixelX/pixelY`, `target_x/target_y`, raw `x/y/z`, and online-map `lat/lng` are supported.
- Keep `frame_interval` minimum behavior at 0.05 seconds for visual modes and 60 Hz for active network coordinate mode.
- Keep `position_backend` values to `auto`, `coordinate`, and `map`.
- Keep `angle_backend` values to `auto`, `directml`, and `cpu`.
- Preserve WebSocket message compatibility: top-level `type`, `version`, `position`, `angle`, `pitch`, `angleConfidence`, `route`, and `timestamp`.
