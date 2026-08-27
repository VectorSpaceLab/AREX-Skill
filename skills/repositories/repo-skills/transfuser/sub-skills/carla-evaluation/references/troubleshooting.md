# CARLA Evaluation Troubleshooting

## Purpose

Use the symptom tables below before changing code or rerunning a long external
evaluation. The safe helpers in this skill do not launch CARLA, Docker, or
cloud services.

## Environment And Evaluator

| Symptom | Likely cause | Action |
|---|---|---|
| `ModuleNotFoundError: carla` | CARLA PythonAPI or egg missing from the active interpreter path | Rebuild the plan with `build_evaluation_command.py`; verify the CARLA 0.9.10.1 PythonAPI and matching egg exist. Remove conflicting CARLA paths. |
| `ModuleNotFoundError: srunner` | `SCENARIO_RUNNER_ROOT` absent or wrong | Point it at the directory containing `srunner`, then regenerate `PYTHONPATH`. |
| `ModuleNotFoundError: leaderboard` | `LEADERBOARD_ROOT` absent or path order wrong | Point it at the directory containing the `leaderboard` package and place it before unrelated installs. |
| Connection timeout at startup | Server absent, wrong host/port, firewall, or CARLA process failed | Check the external server process and port. The command builder cannot probe a running server. |
| `The CARLA server uses the wrong map` | Server world and route town disagree | Stop conflicting clients, restart the external server cleanly, and confirm the route's town. |
| Version message refers to CARLA 0.9.10.1 or newer | Incompatible PythonAPI distribution | Use the repository's pinned 0.9.10.1 server/PythonAPI pair. Do not mix eggs from another installation. |
| A bundled ScenarioRunner marker says 0.9.9 | Stale third-party marker conflicts with the repository evaluation recipe | Follow the public evaluator/README target of 0.9.10.1 for this repository snapshot; record the marker mismatch rather than silently switching servers. |
| Local evaluator fails on `DATAGEN` | Environment variable absent | Use the builder's local mode, which emits `DATAGEN=0`. |
| Local and upstream scores differ | Dense traffic, stop penalty, or local wrapper/criteria semantics differ | Confirm evaluator mode. Do not merge or compare scores without labeling the mode. |

## Agent And Checkpoint Setup

| Symptom | Likely cause | Action |
|---|---|---|
| `Failed - Agent couldn't be set up` | Missing/invalid `args.txt`, no checkpoint, dependency error, wrong team-agent path, or state-dict mismatch | Validate the team/config layout; inspect the external traceback; ensure `args.txt` is JSON and at least one `.pth` exists. |
| State dict keys are missing or unexpected | Submission code strips a seven-character distributed-training prefix | Confirm whether the model was trained with distributed wrapping. A single-GPU checkpoint may require an intentional agent-code adjustment before external evaluation. |
| Sensor configuration rejected | Track and agent sensor suite disagree or local/upstream wrapper limits differ | Confirm `SENSORS` versus `MAP`, evaluator mode, sensor count, and sensor radius before rerunning. |
| Resume unexpectedly starts in the middle | `--resume=False` or `--resume=0` was passed to legacy `argparse` | Those nonempty strings become true. Use the builder with `--resume false`, which omits the flag. |
| Fresh run truncates an existing result | Resume was false and the checkpoint path was reused | Restore a backup or choose a new checkpoint. Inspect plan and checkpoint before an external run. |
| Resume skips or overwrites wrong records | Routes, repetitions, or checkpoint came from another plan | Compare XML route count and `_checkpoint.progress`; resume only an identical plan. |
| Simulation/agent crashed | CARLA, model, GPU, or scenario runtime failed | Preserve the partial checkpoint and traceback. Do not treat command preflight as runtime verification. Inspect JSON, then fix the external dependency before retrying. |

## Result Inspection And Parsing

| Symptom | Likely cause | Action |
|---|---|---|
| JSON inspector exits nonzero | Malformed JSON, missing required field, bad types, inconsistent progress, or strict-mode route failure | Read every reported error. Use normal mode for structural inspection and strict mode only as a success gate. |
| `eligible: true` but failures are present | Eligibility mostly records completeness, not route success | Inspect `entry_status` and every per-route `status`; do not use eligibility alone. |
| `global_record.meta.exceptions` lists completed routes | Source identity-comparison quirk | Trust each record's `status` string rather than the global exceptions list. |
| Parser reports missing/duplicate route ids | Results do not cover the supplied XML evenly | Supply the matching combined XML, or parse each split result against its split XML. Remove accidental duplicates. |
| Parser rejects route count | Completed record count is not a whole number of XML route sets | Recover the missing result or select the correct XML. Do not pad the set with duplicates. |
| Parser aborts on setup/simulation failure | Default `source` policy detected an exact hard-failure status | Repair and rerun that route, or use `allow` only for deliberate forensic analysis. |
| Parser rejects all-zero distance | No route made measurable progress | Per-kilometre metrics are undefined. Diagnose agent setup/startup rather than forcing output. |
| Parser rejects off-road description | Distance could not be extracted safely | Preserve the original event text and repair the producer or analyze manually; do not substitute a guessed distance. |
| Existing `results.csv` or SVG blocks parsing | Safe overwrite guard | Choose a new output directory or use `--overwrite` after reviewing existing outputs. |
| Map generation reports missing PNG | Town-map directory incomplete | Provide `Town01.png` through the towns represented by the result set, or omit `--town-maps` for CSV-only parsing. |
| Map point is out of bounds | Coordinate transform and map asset do not match | Confirm the town-map set belongs to this benchmark snapshot. The event remains in CSV even if it cannot be plotted. |

## Docker And Submission

| Symptom | Likely cause | Action |
|---|---|---|
| Layout checker cannot find Python 2/3 eggs | CARLA PythonAPI package differs from the source staging assumptions | Supply the expected 0.9.10.1 package or deliberately update and test the external packaging recipe. |
| Config directory is outside team code | Source build copies only team code into the image | Move/copy approved model artifacts under the team-code tree before external staging. |
| Empty or missing `.pth` | Model was not staged or copy failed | Restore approved checkpoints; never download automatically from this skill. |
| `args.txt` is invalid | Truncated file or non-JSON training metadata | Regenerate it from the matching training run and validate again. |
| Docker dependency build fails | Legacy Ubuntu/Python/CUDA wheel matrix is unavailable or incompatible | Treat containerization as a separate pinned environment. Resolve versions deliberately; do not upgrade packages blindly. |
| Team-code symlink escapes its root | Docker context may omit or unexpectedly expose host data | Replace it with an explicit reviewed copy inside team code. |
| Alpha login/submission fails | Credentials, authorization, CLI version, split, or service issue | Stop automation. Let an authorized human resolve credentials and approve upload outside this skill. Never paste tokens into diagnostic files. |

## Stop Conditions

Stop and report an external-runtime block when resolution requires downloading
CARLA/models, launching a simulator, using a GPU unavailable to the environment,
building/running Docker, or authenticating/uploading to Alpha. CPU schema,
command, CSV, and layout diagnostics can continue independently.
