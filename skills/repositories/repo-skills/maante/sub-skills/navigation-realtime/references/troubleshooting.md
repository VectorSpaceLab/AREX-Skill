# Navigation and Realtime Troubleshooting

## Coordinate Backend Unavailable

Symptoms:

- `position_backend=coordinate` fails.
- Logs mention coordinate core missing, wrong API version, or capture backend unavailable.
- `auto` mode falls back to visual positioning.

Likely causes:

- The encrypted coordinate core file is missing from the packaged runtime.
- Python ABI/architecture does not match the `.pyd` file.
- Packet capture backend or permissions are missing.
- The game/network protocol changed.

Actions:

- Use `position_backend=map` to force visual fallback when coordinate capture is not required.
- Keep coordinate-mode failures explicit; do not claim coordinate support from visual mode.
- For maintainer fixes, inspect coordinate API version constants and capture backend error messages.

## DirectML or Angle Prediction Issues

Symptoms:

- Angle prediction import/session fails.
- `directml` backend unavailable on Linux or CPU-only environments.
- Navigation turns incorrectly or fails to align.

Actions:

- Use `angle_backend=cpu` only as a fallback or static inspection route; it does not prove DirectML behavior.
- Check ONNX runtime providers and model path availability.
- If direction is wrong while position is correct, debug the angle model separately from route parsing.

## Route Does Not Converge

Symptoms:

- Character walks near a point but never advances.
- Navigation oscillates around a target.
- It starts from the wrong segment position.

Likely causes:

- `tolerance` too small for map-location error.
- Route point coordinate type or source size is wrong.
- `nearest_index` starts midway because current point is closer to a later waypoint.
- Frame interval or stale coordinate data causes delayed control.

Actions:

- Validate route JSON shape with `validate_route_json.py`.
- Increase `tolerance` when map matching is noisy.
- Split long or ambiguous paths into smaller segments.
- Use debug mode only for local diagnosis; it may open OpenCV windows.

## WebSocket Service Issues

Symptoms:

- Online map cannot connect.
- Port already in use.
- Client receives stale/null positions.

Actions:

- Confirm the configured port; default is 14514.
- The service binds `0.0.0.0`; local clients should use `ws://127.0.0.1:<port>`.
- Check whether route runner is publishing frames and whether position backend is finding coordinates.
- Stop the task to close the server cleanly before restarting on the same port.

## Realtime Task Loop Stuck

Symptoms:

- RealTime never exits after the user stops.
- Enabled subnodes are not being run.

Checks:

- `RealTimeTaskAction` expects a JSON object with a non-empty `nodes` list.
- Loop should run until `context.tasker.stopping` becomes true.
- Task options should enable/disable nodes through Pipeline overrides; inspect the holder node's effective `next` list.

## Dataset Recorder Issues

Symptoms:

- Output is empty or labels are all none.
- Import fails on non-Windows.
- Disk fills with images.

Actions:

- This recorder is a live-data tool, not a unit test. Use bounded `duration_seconds` and a deliberate output directory.
- It depends on Windows key-state APIs for labels.
- Check start delay, screenshot availability, and stopping behavior.
