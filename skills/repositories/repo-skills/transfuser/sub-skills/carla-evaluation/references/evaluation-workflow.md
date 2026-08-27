# Evaluation Workflow

## Purpose

Use this reference to construct and review a TransFuser CARLA evaluator command.
The bundled builder emits shell or JSON; it never starts a simulator or evaluator.

## External Runtime Contract

A real run requires all of the following outside this skill:

- CARLA 0.9.10.1, including `CarlaUE4.sh` and a PythonAPI compatible with the
  Python environment used by the evaluator.
- A CARLA server reachable at the selected host and port (the repository launch
  examples use port `2000`).
- Matching ScenarioRunner and leaderboard trees.
- The TransFuser team agent and a model configuration directory containing
  `args.txt` and one or more model checkpoints.
- CUDA-capable inference dependencies for the learned TransFuser agent.

The repository setup targets Python 3.7. Its evaluator accepts CARLA package
version `leaderboard` or a version at least 0.9.10, while its public evaluation
recipe pins the simulator to 0.9.10.1. Use 0.9.10.1 for reproducibility.

## Environment And CLI Mapping

The thin repository launchers translate environment variables into evaluator
arguments. The bundled builder exposes the shorter concept name and emits the
actual launcher name where they differ.

| Concept | Repository environment variable | Evaluator argument | Meaning |
|---|---|---|---|
| CARLA root | `CARLA_ROOT` | indirect | Simulator installation and PythonAPI root |
| ScenarioRunner | `SCENARIO_RUNNER_ROOT` | indirect | Makes `srunner` importable |
| leaderboard | `LEADERBOARD_ROOT` | evaluator path | Makes `leaderboard` importable and selects evaluator |
| import path | `PYTHONPATH` | indirect | CARLA PythonAPI, CARLA egg, ScenarioRunner, leaderboard, then inherited path |
| scenarios | `SCENARIOS` | `--scenarios` | Scenario annotation JSON |
| routes | `ROUTES` | `--routes` | Combined or split route XML |
| repetitions | `REPETITIONS` | `--repetitions` | Repeats each XML route; must be positive |
| track | `CHALLENGE_TRACK_CODENAME` | `--track` | `SENSORS` or `MAP`; the builder also reports alias `TRACK` |
| checkpoint | `CHECKPOINT_ENDPOINT` | `--checkpoint` | Result/checkpoint JSON; the builder also reports alias `CHECKPOINT` |
| agent | `TEAM_AGENT` | `--agent` | Python agent entry file |
| config | `TEAM_CONFIG` | `--agent-config` | Model/config directory or agent-specific config |
| debug | `DEBUG_CHALLENGE` | `--debug` | Integer debug level; the builder also reports alias `DEBUG` |
| resume | `RESUME` | `--resume` when true | Continue from `_checkpoint.progress` |
| local mode guard | `DATAGEN=0` | indirect | Required by local evaluator modules to select evaluation behavior |

The emitted `PYTHONPATH` puts the CARLA PythonAPI, matching CARLA egg when
found, ScenarioRunner, and leaderboard ahead of the inherited path. If imports
still resolve to another CARLA installation, inspect the active interpreter and
remove the conflicting path rather than appending more duplicate entries.

## Build A Command Plan

Run from the `carla-evaluation` skill directory:

```bash
python scripts/build_evaluation_command.py \
  --repo-root /path/to/transfuser \
  --carla-root /path/to/CARLA_0.9.10.1 \
  --mode local \
  --route-set longest6 \
  --team-config /path/to/model_ckpt/transfuser \
  --checkpoint /path/to/results/transfuser_longest6.json \
  --track SENSORS \
  --repetitions 1 \
  --resume true \
  --format shell
```

Preflight is strict by default. `--allow-missing` is for planning on a machine
that does not contain the external runtime; warnings remain unresolved and the
printed command is not runnable evidence. Use `--format json` when another tool
needs the environment, argument vector, warnings, and mode as structured data.

For one Longest6 route, replace the route selection with
`--route-set split --route-index 15`. For a custom pair, use
`--route-set custom --routes /path/routes.xml --scenarios /path/scenarios.json`.

## Local Versus Upstream Evaluator

### Local evaluator

Select `--mode local` for the repository's Longest6 semantics. The local stack:

- Requests 500 background vehicles when `DATAGEN=0`, effectively attempting to
  fill all simulator spawn points rather than using the upstream town-specific
  counts.
- Sets the stop-sign penalty multiplier to `1.0`, so stop infractions are
  recorded but do not reduce the composed score. The upstream multiplier is
  `0.8`.
- Uses local scenario criteria, manager, and agent wrapper variants. These also
  expand supported data-generation sensors, increase the allowed sensor radius
  from 3 m to 10 m, and adjust camera/LiDAR/GNSS behavior.
- Requires `DATAGEN` to be defined; evaluation must use `DATAGEN=0`.

### Upstream evaluator

Select `--mode upstream` only when upstream leaderboard semantics are intended.
It uses town-specific background traffic counts and penalizes stop infractions.
Running Longest6 route files through it does not reproduce the documented local
benchmark semantics. Label any upstream score clearly and do not compare it as
if it were a local Longest6 result.

## Resume And Checkpoint Discipline

The evaluator's legacy `--resume` option uses `type=bool`. Passing any nonempty
text, including `False` or `0`, evaluates as true. The bundled builder therefore:

- Emits `--resume=True` only for `--resume true`.
- Omits `--resume` for `--resume false`, allowing the evaluator default to stay
  false.

On a fresh run, the evaluator clears the checkpoint file and writes initial
route-index state. On resume, it reads `_checkpoint.progress[0]` and starts at
that route index, while the statistics manager reloads existing route records.
Before resuming, verify that routes, scenarios, repetitions, evaluator mode,
agent, and config are the same as the run that created the checkpoint. Copy a
checkpoint before experimentation; do not reuse one across incompatible plans.

## What Preflight Does Not Prove

The command builder checks local paths and argument consistency only. It cannot
prove that:

- The CARLA server is running or serves the expected map.
- CARLA PythonAPI binary compatibility is correct.
- GPU libraries and model checkpoint tensors can load.
- Agent sensors match the selected track.
- A route completes or a score is valid.

Use [troubleshooting.md](troubleshooting.md) for the next diagnostic step and
[result-schema.md](result-schema.md) after a run produces a checkpoint.
