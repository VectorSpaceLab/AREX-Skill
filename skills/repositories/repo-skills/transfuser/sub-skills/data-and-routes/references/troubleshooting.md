# Data And Routes Troubleshooting

The checks in this sub-skill are local and side-effect free. They do not start
CARLA or contact a server. Keep errors classified as **schema**, **path**,
**external runtime**, or **collection output** before retrying.

## Schema and pairing

| Symptom | Likely cause | Action |
|---|---|---|
| XML root/route/waypoint error | Wrong file, truncated XML, missing `town`/`id`, or nonnumeric transform | Run `validate_route_files.py --format json`; repair or regenerate the file, then recheck. |
| JSON has no `available_scenarios` | Evaluation JSON or an unrelated annotation was supplied | Use the training scenario annotation shape, not a result/checkpoint JSON. |
| Scenario event lacks `transform` | Partial or hand-edited annotation | Regenerate from the matching map or remove the event deliberately; do not invent coordinates. |
| Route town not in scenario JSON | Pair from different town/map or wrong directory | Match town and logical ScenarioN before external generation. |
| Valid route but no scenario match | Trigger is outside the interpolated route, yaw/position exceeds the matcher tolerance, or turn subtype is invalid | Rebuild with the same CARLA map/version and inspect the route/trigger visualization. Structural validation cannot detect this. |
| Route ids are non-contiguous | Generator retained source ids after filtering, especially Scenario7/8/9 | This is allowed; require uniqueness within the file, not contiguity. |
| Lane-change label looks reversed | `lr`/`rl` convention was interpreted as endpoint-first | Interpret the first letter as the earlier lateral direction and second as later; inspect midpoint and endpoint. |

## Runtime and import path

| Symptom | Likely cause | Action |
|---|---|---|
| `ModuleNotFoundError: carla` | CARLA PythonAPI/egg not on the selected interpreter path | Check the actual 0.9.10.1 PythonAPI and rebuild the plan with the CARLA root. Do not mix versions. |
| `ModuleNotFoundError: srunner` or `leaderboard` | Root points at the wrong directory or `PYTHONPATH` order is stale | Set the roots to directories containing those packages; put them after CARLA and before conflicting installs. |
| Connection refused/timeout | No server, wrong port, server still loading a map, or firewall | Stop. Verify the separately managed server and port; the safe scripts cannot probe or fix it. |
| Generator loads wrong town | A shared server has an old world or multiple clients changed it | Use one clean server/world per town and confirm the route `town` attribute. |
| Generator fails in `utils`/route planner | ScenarioRunner/leaderboard/CARLA API mismatch | Compare all three versions and the Python version; do not replace one package with an unverified modern API. |
| Visualization fails in pygame/headless mode | Display, SDL, or map image cache unavailable | Prepare a documented headless graphics environment or use CPU schema checks only. |

## Dataset output

| Symptom | Likely cause | Action |
|---|---|---|
| Missing `measurements/` | AutoPilot output was not enabled or collection failed before the first save | Inspect simulator/evaluator logs and `SAVE_PATH`; do not fill measurements with placeholders. |
| Missing `topdown`, `label_raw`, or sensor directory | DataAgent setup did not complete or output was interrupted | Fix the CARLA/agent setup, use a fresh route output, and recollect. |
| Frame ids differ across modalities | Sensor callback/dropout, interrupted copy, or mixed runs | Remove/quarantine the route and recollect or restore a complete atomic snapshot. |
| Only a few frames exist | Route ended, server crashed, or `save_freq`/output path was changed | Validate with `--require-windows`; a basic one-frame fixture is not training-ready. |
| JSON measurement malformed | Interrupted write or incompatible agent version | Parse it with the validator and compare agent/runtime versions. Never silently skip a corrupt frame. |
| Labels are empty lists | No actor labels were captured or a placeholder fixture was used | Treat as a data-quality warning; validate that the ego/actor label contract is met for the intended task. |
| Disk fills during collection | Image/LiDAR modalities are large; the full public data target is about 210 GB | Stop safely, check free space and route output, and reduce scope before restarting. Never delete raw data automatically. |
| Dataset loader returns zero windows | Wrong scenario/town nesting, missing modality, or fewer than ten synchronized frames with defaults | Run the layout validator with `--require-windows`, then hand off model/config issues to `model-training`. |

## Recovery and safety

Preserve the first failing XML/JSON, command plan, server version, town,
route/scenario pair, and output listing. Do not rerun a large collection merely
to obtain a clean log. Use a new `SAVE_PATH` after partial output unless the
operator has verified resume semantics. A valid route command, successful
schema parse, or populated directory is not evidence that CARLA generation
passed.

Report `BLOCKED_REQUIRED_BACKEND: CARLA_0.9.10.1_RUNTIME` when the simulator or
matching Python API is unavailable. CPU validation may still pass; the block
only clears after a real external generation/visualization trial is logged.
