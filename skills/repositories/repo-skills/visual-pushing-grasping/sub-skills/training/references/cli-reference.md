# CLI reference

This is the literal `main.py` parser contract at the pinned historical source
revision. Long options use underscores exactly as shown. The parser itself is
permissive in a few places; the safe validator intentionally rejects or warns
before those values reach the long-running loop. `main.py` and its defaults are
source evidence; the runtime graph does not bundle that application.

## Exact flags and defaults

| Flag | Type/action | Source default | Operational meaning |
|---|---|---:|---|
| `--is_sim` | boolean | `False` | Use the simulation adapter instead of the real-robot adapter. |
| `--obj_mesh_dir` | string | `objects/blocks` | Simulation mesh directory. Ignored for real mode. |
| `--num_obj` | integer | `10` | Number of simulation objects. |
| `--tcp_host_ip` | string | `<operator-approved-controller-host>` | UR5 TCP client address in real mode. |
| `--tcp_port` | integer | `30002` | UR5 TCP client port. |
| `--rtc_host_ip` | string | `<operator-approved-controller-host>` | UR5 real-time client address. |
| `--rtc_port` | integer | `30003` | UR5 real-time client port. |
| `--heightmap_resolution` | float | `0.002` | Heightmap meters per pixel. |
| `--random_seed` | integer | `1234` | NumPy seed used by the main program. |
| `--cpu` | boolean | `False` | Force CPU model execution even when CUDA is visible. |
| `--method` | string | `reinforcement` | `reactive` classification or `reinforcement` Q-learning. |
| `--push_rewards` | boolean | `False` | Include immediate change reward for reinforcement pushes. |
| `--future_reward_discount` | float | `0.5` | Discount factor used for future Q targets. |
| `--experience_replay` | boolean | `False` | Enable prioritized replay during training. |
| `--heuristic_bootstrap` | boolean | `False` | Use handcrafted depth heuristics after repeated failures. |
| `--explore_rate_decay` | boolean | `False` | Decay training exploration from 0.5 toward 0.1. |
| `--grasp_only` | boolean | `False` | Force the selected primitive to grasp. |
| `--is_testing` | boolean | `False` | Enter testing mode rather than training mode. |
| `--max_test_trials` | integer | `30` | Maximum test runs per case/scenario. |
| `--test_preset_cases` | boolean | `False` | Ask the environment to use preset test cases. |
| `--test_preset_file` | string | `test-10-obj-01.txt` | Preset file when preset mode is enabled. |
| `--load_snapshot` | boolean | `False` | Load a state-dict snapshot before execution. |
| `--snapshot_file` | string | `None` | Snapshot path; required in practice with `--load_snapshot`. |
| `--continue_logging` | boolean | `False` | Reuse a prior session and preload transition logs. |
| `--logging_directory` | string | `None` | Prior session when continuing; otherwise source uses absolute `logs`. |
| `--save_visualizations` | boolean | `False` | Save push/grasp affordance images; adds substantial I/O. |

The source computes `obj_mesh_dir`, `test_preset_file`, `snapshot_file`, and
`logging_directory` as absolute paths only when their corresponding mode is
active. With no `--continue_logging`, `Logger` creates a timestamped child
under the effective `logs` parent. With `--continue_logging`, a missing
`--logging_directory` reaches `abspath(None)` and fails before a useful
resume diagnostic; catch it with the validator first.

## Method and mode combinations

- `reactive` uses class-affordance maps and ignores `--push_rewards` in
  `main.py`; remove that flag to avoid a misleading command.
- `reinforcement` is the parser default. `--push_rewards` changes the push
  target semantics described in [model-and-training.md](model-and-training.md).
- `--is_testing` sets exploration probability to zero and bypasses replay.
  `--experience_replay` and `--explore_rate_decay` may parse, but have no
  effect in that mode; the validator reports this rather than silently
  implying a test-time benefit.
- `--grasp_only` is compatible with both methods and takes precedence over
  push-versus-grasp comparison.
- `--test_preset_cases` requires an existing readable preset file and an
  environment that understands the preset format. It does not make a real
  robot or simulator available.
- `--load_snapshot` requires an existing non-empty file. The source calls
  `torch.load(snapshot_file)` without `map_location`; a CPU test of a GPU-saved
  old snapshot may fail even when the file exists.
- `--continue_logging` requires the prior session directory and its transition
  logs. It is a resume contract, not merely a place to write new logs.

## Safe command construction

Use an operator-provided application copy and a pre-approved environment. The
following is a *construction template*, not an assertion that the historical
loop works on current software:

```bash
# Side-effect-free preflight; no torch import, socket, simulator, or weight download.
# <skill-root> contains the root SKILL.md; the other placeholders are external.
python <skill-root>/sub-skills/training/scripts/check_training_config.py \
  --is_sim --obj_mesh_dir <MESH_DIR> --method reinforcement --cpu \
  --is_testing --max_test_trials 1 \
  --load_snapshot --snapshot_file <SNAPSHOT> \
  --test_preset_cases --test_preset_file <CASE> \
  --logging_directory <LOG_DIR>
```

For the guarded application launch in a separately prepared application
copy (never as a verification shortcut from the historical evidence checkout),
preserve the same method, snapshot, test case, CPU choice, and trial bound:

```bash
python <APP_ROOT>/main.py \
  --is_sim --obj_mesh_dir <MESH_DIR> --method reinforcement --cpu \
  --is_testing --max_test_trials 1 \
  --load_snapshot --snapshot_file <SNAPSHOT> \
  --test_preset_cases --test_preset_file <CASE> \
  --logging_directory <LOG_DIR>
```

`<APP_ROOT>` is an operator-supplied, separately reviewed application copy;
`<MESH_DIR>`, `<CASE>`, `<SNAPSHOT>`, and `<LOG_DIR>` are also external
operator paths. The runtime graph supplies no `main.py` loop.

This is a guarded launch template, not a full-loop success claim. Do not add
`--continue_logging` unless the logging path is a complete prior session.
Before launch, separately confirm that the simulator is already running and
its scene/mesh assets match the policy, or that the physical path has an
operator-approved robot/camera safety plan. Stop before action execution if
any of those prerequisites is absent. The source artifact itself is not a
runtime dependency of this skill.

For a training resume, the corresponding preflight shape is:

```bash
python <skill-root>/sub-skills/training/scripts/check_training_config.py \
  --is_sim --obj_mesh_dir <MESH_DIR> --method reinforcement --cpu \
  --push_rewards --experience_replay --explore_rate_decay \
  --load_snapshot --snapshot_file <SNAPSHOT> \
  --continue_logging --logging_directory <SESSION>
```

The validator does not inspect a PyTorch state dict, import the source, or
start a training thread. A successful validation means only that the paths and
flags are internally coherent.

## Safe stop boundaries

Do not validate by running the source application's `<APP_ROOT>/main.py`
with `--is_testing` alone: testing still constructs a robot adapter and loops
on camera data. Do not run the simulator, real robot, calibration, camera
server, or long training as an import/help smoke. For first execution use one
trial, an explicit snapshot, and a manual abort plan; treat any network,
camera, model-load, or action-selection warning as a stop condition.
